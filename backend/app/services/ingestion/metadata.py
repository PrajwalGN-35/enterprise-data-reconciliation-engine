from pathlib import Path

import pandas as pd


def generate_dataset_metadata(
    file_path: str,
    dataframe: pd.DataFrame
) -> dict:
    """
    Generate basic metadata for an ingested dataset.
    """

    path = Path(file_path)

    return {
        "file_name": path.name,
        "file_type": path.suffix.lower().replace(".", ""),
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": list(dataframe.columns),
        "data_types": {
            column: str(dtype)
            for column, dtype in dataframe.dtypes.items()
        },
        "missing_values": {
            column: int(count)
            for column, count in dataframe.isna().sum().items()
        },
        "duplicate_rows": int(dataframe.duplicated().sum()),
    }