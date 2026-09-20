from fastapi import FastAPI

from app.api.health import router as health_router
from app.api.datasets.upload import router as dataset_router
from app.api.reconciliation import router as reconciliation_router
from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version=settings.app_version,
    description=(
        "Enterprise data quality and cross-system "
        "reconciliation platform."
    ),
)

app.include_router(health_router)
app.include_router(dataset_router)
app.include_router(reconciliation_router)


@app.get("/")
def root():
    return {
        "message": "Enterprise Data Reconciliation Engine API",
        "version": settings.app_version,
        "status": "running",
    }
