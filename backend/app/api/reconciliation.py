from dataclasses import asdict
from pathlib import Path
import json
import tempfile
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy import func
from sqlalchemy.orm import Session

from app.api.reconciliation_history_schemas import (
    AuditLogResponse,
    ReconciliationAuditResponse,
    ReconciliationRunDetailResponse,
    ReconciliationRunHistoryItem,
    ReconciliationRunHistoryResponse,
)
from app.api.reconciliation_schemas import ReconciliationRunResponse
from app.core.database import SessionLocal, get_db
from app.models import AuditLog, ReconciliationRun
from app.services.ingestion.loader import (
    DatasetIngestionError,
    load_dataset,
)
from app.services.reconciliation.orchestrator import (
    run_reconciliation_workflow,
)

router = APIRouter(
    prefix="/reconciliation",
    tags=["Reconciliation"],
)

ALLOWED_EXTENSIONS = {".csv", ".xlsx", ".json"}


def _parse_fields(value: str, field_name: str) -> list[str]:
    try:
        fields = json.loads(value)
    except json.JSONDecodeError as exc:
        raise HTTPException(
            status_code=400,
            detail=f"{field_name} must be a valid JSON array.",
        ) from exc

    if (
        not isinstance(fields, list)
        or not fields
        or not all(
            isinstance(field, str) and field.strip()
            for field in fields
        )
    ):
        raise HTTPException(
            status_code=400,
            detail=(
                f"{field_name} must contain at least one "
                "non-empty field name."
            ),
        )

    return [field.strip() for field in fields]


async def _save_upload(
    upload: UploadFile,
    directory: Path,
) -> Path:
    extension = Path(upload.filename or "").suffix.lower()

    if extension not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. Allowed types: "
                "CSV, XLSX, JSON."
            ),
        )

    contents = await upload.read()

    if not contents:
        raise HTTPException(
            status_code=400,
            detail=f"Uploaded file '{upload.filename}' is empty.",
        )

    directory.mkdir(parents=True, exist_ok=True)

    file_path = directory / f"upload{extension}"
    file_path.write_bytes(contents)

    return file_path


def _persist_failed_run(
    db: Session,
    run: ReconciliationRun,
    source_file_name: str,
    target_file_name: str,
    started_at: datetime,
    error_type: str,
    error_message: str,
) -> None:
    db.rollback()

    failed_db = SessionLocal()

    try:
        failed_run = ReconciliationRun(
            id=run.id,
            source_file_name=source_file_name,
            target_file_name=target_file_name,
            status="failed",
            started_at=started_at,
            completed_at=datetime.now(timezone.utc),
        )

        failed_db.add(failed_run)
        failed_db.flush()

        failed_db.add(
            AuditLog(
                action="reconciliation_failed",
                entity_type="reconciliation_run",
                entity_id=failed_run.id,
                details=json.dumps(
                    {
                        "source_file_name": source_file_name,
                        "target_file_name": target_file_name,
                        "status": "failed",
                        "error_type": error_type,
                        "error": error_message,
                    }
                ),
            )
        )

        failed_db.commit()
    finally:
        failed_db.close()


@router.post(
    "/run",
    response_model=ReconciliationRunResponse,
)
async def run_reconciliation(
    source_file: UploadFile = File(...),
    target_file: UploadFile = File(...),
    matching_fields: str = Form(...),
    reconciliation_fields: str = Form(...),
    db: Session = Depends(get_db),
):
    parsed_matching_fields = _parse_fields(
        matching_fields,
        "matching_fields",
    )

    parsed_reconciliation_fields = _parse_fields(
        reconciliation_fields,
        "reconciliation_fields",
    )

    started_at = datetime.now(timezone.utc)

    run = ReconciliationRun(
        source_file_name=source_file.filename or "unknown",
        target_file_name=target_file.filename or "unknown",
        status="running",
        started_at=started_at,
    )

    db.add(run)
    db.flush()

    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)

        try:
            source_path = await _save_upload(
                source_file,
                directory / "source",
            )

            target_path = await _save_upload(
                target_file,
                directory / "target",
            )

            source_dataframe = load_dataset(str(source_path))
            target_dataframe = load_dataset(str(target_path))

            workflow = run_reconciliation_workflow(
                source_dataframe=source_dataframe,
                target_dataframe=target_dataframe,
                matching_fields=parsed_matching_fields,
                reconciliation_fields=parsed_reconciliation_fields,
            )

            completed_at = datetime.now(timezone.utc)
            summary = workflow.summary

            run.status = "completed"
            run.completed_at = completed_at
            run.source_record_count = summary.source_record_count
            run.target_record_count = summary.target_record_count
            run.matched_record_count = summary.matched_record_count
            run.discrepancy_record_count = summary.discrepancy_record_count
            run.missing_target_record_count = summary.missing_target_record_count
            run.review_required_record_count = summary.review_required_record_count
            run.total_discrepancy_count = summary.total_discrepancy_count
            run.reconciliation_percentage = summary.reconciliation_percentage
            run.exception_percentage = summary.exception_percentage
            run.field_discrepancy_counts = summary.field_discrepancy_counts

            audit_log = AuditLog(
                action="reconciliation_completed",
                entity_type="reconciliation_run",
                entity_id=run.id,
                details=json.dumps(
                    {
                        "source_file_name": source_file.filename or "unknown",
                        "target_file_name": target_file.filename or "unknown",
                        "status": "completed",
                        "source_record_count": summary.source_record_count,
                        "target_record_count": summary.target_record_count,
                        "matched_record_count": summary.matched_record_count,
                        "discrepancy_record_count": summary.discrepancy_record_count,
                        "total_discrepancy_count": summary.total_discrepancy_count,
                    }
                ),
            )

            db.add(audit_log)
            db.commit()
            db.refresh(run)

            encoded_workflow = jsonable_encoder(
                asdict(workflow)
            )

            return {
                "status": "success",
                "run_id": run.id,
                "source_file_name": source_file.filename or "unknown",
                "target_file_name": target_file.filename or "unknown",
                **encoded_workflow,
            }

        except DatasetIngestionError as exc:
            _persist_failed_run(
                db=db,
                run=run,
                source_file_name=source_file.filename or "unknown",
                target_file_name=target_file.filename or "unknown",
                started_at=started_at,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        except ValueError as exc:
            _persist_failed_run(
                db=db,
                run=run,
                source_file_name=source_file.filename or "unknown",
                target_file_name=target_file.filename or "unknown",
                started_at=started_at,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        except HTTPException as exc:
            _persist_failed_run(
                db=db,
                run=run,
                source_file_name=source_file.filename or "unknown",
                target_file_name=target_file.filename or "unknown",
                started_at=started_at,
                error_type="HTTPException",
                error_message=str(exc.detail),
            )
            raise

        except Exception as exc:
            _persist_failed_run(
                db=db,
                run=run,
                source_file_name=source_file.filename or "unknown",
                target_file_name=target_file.filename or "unknown",
                started_at=started_at,
                error_type=type(exc).__name__,
                error_message=str(exc),
            )
            raise HTTPException(
                status_code=500,
                detail=f"Reconciliation failed: {exc}",
            ) from exc


@router.get(
    "/runs",
    response_model=ReconciliationRunHistoryResponse,
)
def get_reconciliation_runs(
    limit: int = 20,
    offset: int = 0,
    db: Session = Depends(get_db),
):
    if limit < 1 or limit > 100:
        raise HTTPException(
            status_code=400,
            detail="limit must be between 1 and 100.",
        )

    if offset < 0:
        raise HTTPException(
            status_code=400,
            detail="offset must be greater than or equal to 0.",
        )

    total = (
        db.query(func.count(ReconciliationRun.id))
        .scalar()
        or 0
    )

    runs = (
        db.query(ReconciliationRun)
        .order_by(ReconciliationRun.created_at.desc())
        .offset(offset)
        .limit(limit)
        .all()
    )

    return ReconciliationRunHistoryResponse(
        total=total,
        limit=limit,
        offset=offset,
        runs=[
            ReconciliationRunHistoryItem(
                run_id=run.id,
                source_file_name=run.source_file_name,
                target_file_name=run.target_file_name,
                status=run.status,
                started_at=run.started_at.isoformat(),
                completed_at=(
                    run.completed_at.isoformat()
                    if run.completed_at
                    else None
                ),
                source_record_count=run.source_record_count,
                target_record_count=run.target_record_count,
                matched_record_count=run.matched_record_count,
                discrepancy_record_count=run.discrepancy_record_count,
                missing_target_record_count=run.missing_target_record_count,
                review_required_record_count=run.review_required_record_count,
                total_discrepancy_count=run.total_discrepancy_count,
                reconciliation_percentage=run.reconciliation_percentage,
                exception_percentage=run.exception_percentage,
            )
            for run in runs
        ],
    )


@router.get(
    "/runs/{run_id}",
    response_model=ReconciliationRunDetailResponse,
)
def get_reconciliation_run(
    run_id: str,
    db: Session = Depends(get_db),
):
    run = (
        db.query(ReconciliationRun)
        .filter(ReconciliationRun.id == run_id)
        .first()
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Reconciliation run '{run_id}' not found.",
        )

    return ReconciliationRunDetailResponse(
        run_id=run.id,
        source_file_name=run.source_file_name,
        target_file_name=run.target_file_name,
        status=run.status,
        started_at=run.started_at.isoformat(),
        completed_at=(
            run.completed_at.isoformat()
            if run.completed_at
            else None
        ),
        source_record_count=run.source_record_count,
        target_record_count=run.target_record_count,
        matched_record_count=run.matched_record_count,
        discrepancy_record_count=run.discrepancy_record_count,
        missing_target_record_count=run.missing_target_record_count,
        review_required_record_count=run.review_required_record_count,
        total_discrepancy_count=run.total_discrepancy_count,
        reconciliation_percentage=run.reconciliation_percentage,
        exception_percentage=run.exception_percentage,
        field_discrepancy_counts=run.field_discrepancy_counts or {},
    )


@router.get(
    "/runs/{run_id}/audit",
    response_model=ReconciliationAuditResponse,
)
def get_reconciliation_audit(
    run_id: str,
    db: Session = Depends(get_db),
):
    run = (
        db.query(ReconciliationRun)
        .filter(ReconciliationRun.id == run_id)
        .first()
    )

    if run is None:
        raise HTTPException(
            status_code=404,
            detail=f"Reconciliation run '{run_id}' not found.",
        )

    audit_logs = (
        db.query(AuditLog)
        .filter(AuditLog.entity_id == run_id)
        .order_by(AuditLog.created_at.desc())
        .all()
    )

    return ReconciliationAuditResponse(
        run_id=run_id,
        audit_logs=[
            AuditLogResponse(
                id=audit.id,
                action=audit.action,
                entity_type=audit.entity_type,
                entity_id=audit.entity_id,
                details=audit.details,
                created_at=audit.created_at.isoformat(),
            )
            for audit in audit_logs
        ],
    )
