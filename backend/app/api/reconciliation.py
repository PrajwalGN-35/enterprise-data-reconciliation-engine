from dataclasses import asdict
from datetime import datetime, timezone
from pathlib import Path
import json
import tempfile

from fastapi import APIRouter, Depends, File, Form, HTTPException, UploadFile
from fastapi.encoders import jsonable_encoder
from sqlalchemy.orm import Session

from app.api.reconciliation_schemas import ReconciliationRunResponse
from app.core.database import get_db
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

    with tempfile.TemporaryDirectory() as temporary_directory:
        directory = Path(temporary_directory)

        source_path = await _save_upload(
            source_file,
            directory / "source",
        )

        target_path = await _save_upload(
            target_file,
            directory / "target",
        )

        try:
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

            run = ReconciliationRun(
                source_file_name=(
                    source_file.filename or "unknown"
                ),
                target_file_name=(
                    target_file.filename or "unknown"
                ),
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                source_record_count=(
                    summary.source_record_count
                ),
                target_record_count=(
                    summary.target_record_count
                ),
                matched_record_count=(
                    summary.matched_record_count
                ),
                discrepancy_record_count=(
                    summary.discrepancy_record_count
                ),
                missing_target_record_count=(
                    summary.missing_target_record_count
                ),
                review_required_record_count=(
                    summary.review_required_record_count
                ),
                total_discrepancy_count=(
                    summary.total_discrepancy_count
                ),
                reconciliation_percentage=(
                    summary.reconciliation_percentage
                ),
                exception_percentage=(
                    summary.exception_percentage
                ),
                field_discrepancy_counts=(
                    summary.field_discrepancy_counts
                ),
            )

            db.add(run)
            db.flush()

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
                "source_file_name": (
                    source_file.filename or "unknown"
                ),
                "target_file_name": (
                    target_file.filename or "unknown"
                ),
                **encoded_workflow,
            }

        except DatasetIngestionError as exc:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        except ValueError as exc:
            db.rollback()
            raise HTTPException(
                status_code=400,
                detail=str(exc),
            ) from exc

        except HTTPException:
            db.rollback()
            raise

        except Exception as exc:
            db.rollback()
            raise HTTPException(
                status_code=500,
                detail=f"Reconciliation failed: {exc}",
            ) from exc

