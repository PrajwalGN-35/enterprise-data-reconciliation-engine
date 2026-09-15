from pathlib import Path

import pandas as pd


SUPPORTED_EXTENSIONS = {".csv", ".xlsx", ".json"}


class DatasetIngestionError(Exception):
    """Raised when a dataset cannot be ingested safely."""


def load_dataset(file_path: str) -> pd.DataFrame:
    """
    Load a supported dataset into a Pandas DataFrame.

    Supported formats:
    - CSV
    - Excel (.xlsx)
    - JSON
    """

    path = Path(file_path)

    if not path.exists():
        raise DatasetIngestionError(
            f"Dataset file not found: {path}"
        )

    if not path.is_file():
        raise DatasetIngestionError(
            f"Dataset path is not a file: {path}"
        )

    extension = path.suffix.lower()

    if extension not in SUPPORTED_EXTENSIONS:
        raise DatasetIngestionError(
            f"Unsupported file type: {extension}. "
            f"Supported types: {sorted(SUPPORTED_EXTENSIONS)}"
        )

    try:
        if extension == ".csv":
            dataframe = pd.read_csv(path)

        elif extension == ".xlsx":
            dataframe = pd.read_excel(path)

        elif extension == ".json":
            dataframe = pd.read_json(path)

        else:
            raise DatasetIngestionError(
                f"Unsupported file type: {extension}"
            )

    except Exception as exc:
        raise DatasetIngestionError(
            f"Failed to read dataset '{path.name}': {exc}"
        ) from exc

    if dataframe.empty:
        raise DatasetIngestionError(
            f"Dataset '{path.name}' is empty."
        )

    return dataframe