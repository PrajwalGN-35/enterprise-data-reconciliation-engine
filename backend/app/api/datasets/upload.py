from pathlib import Path
import uuid

from fastapi import APIRouter, File, UploadFile, HTTPException

from app.services.ingestion.loader import (
    load_dataset,
    DatasetIngestionError,
)
from app.services.ingestion.metadata import (
    generate_dataset_metadata,
)
from app.services.ingestion.profiler import (
    profile_dataset,
)
from app.services.ingestion.quality import (
    calculate_quality_summary,
)


router = APIRouter(
    prefix="/datasets",
    tags=["Datasets"],
)


PROJECT_ROOT = Path(__file__).resolve().parents[4]
UPLOAD_DIR = PROJECT_ROOT / "data" / "uploads"


@router.post("/upload")
async def upload_dataset(
    file: UploadFile = File(...)
):
    """
    Upload a dataset and return metadata,
    profiling information, and quality summary.
    """

    allowed_extensions = {
        ".csv",
        ".xlsx",
        ".json",
    }

    extension = Path(file.filename or "").suffix.lower()

    if extension not in allowed_extensions:
        raise HTTPException(
            status_code=400,
            detail=(
                "Unsupported file type. "
                "Allowed types: CSV, XLSX, JSON."
            ),
        )

    UPLOAD_DIR.mkdir(
        parents=True,
        exist_ok=True,
    )

    safe_filename = (
        f"{uuid.uuid4().hex}"
        f"{extension}"
    )

    file_path = UPLOAD_DIR / safe_filename

    try:
        contents = await file.read()

        if not contents:
            raise HTTPException(
                status_code=400,
                detail="Uploaded file is empty.",
            )

        file_path.write_bytes(contents)

        dataframe = load_dataset(
            str(file_path)
        )

        metadata = generate_dataset_metadata(
            str(file_path),
            dataframe,
        )

        profile = profile_dataset(
            dataframe
        )

        quality = calculate_quality_summary(
            dataframe
        )

        return {
            "status": "success",
            "original_file_name": file.filename,
            "stored_file_name": safe_filename,
            "metadata": metadata,
            "profile": profile,
            "quality": quality,
        }

    except DatasetIngestionError as exc:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=400,
            detail=str(exc),
        ) from exc

    except HTTPException:
        if file_path.exists():
            file_path.unlink()

        raise

    except Exception as exc:
        if file_path.exists():
            file_path.unlink()

        raise HTTPException(
            status_code=500,
            detail=f"Dataset processing failed: {exc}",
        ) from exc