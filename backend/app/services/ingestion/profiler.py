import pandas as pd


def profile_dataset(dataframe: pd.DataFrame) -> dict:
    """
    Generate basic statistical and quality profiling
    information for a dataset.
    """

    profile = {
        "row_count": int(len(dataframe)),
        "column_count": int(len(dataframe.columns)),
        "columns": {}
    }

    for column in dataframe.columns:
        series = dataframe[column]

        column_profile = {
            "data_type": str(series.dtype),
            "missing_count": int(series.isna().sum()),
            "missing_percentage": float(
                (series.isna().sum() / len(dataframe)) * 100
            ),
            "unique_count": int(series.nunique(dropna=True)),
        }

        if pd.api.types.is_numeric_dtype(series):
            column_profile.update({
                "min": float(series.min()),
                "max": float(series.max()),
                "mean": float(series.mean()),
                "median": float(series.median()),
            })

        profile["columns"][column] = column_profile

    return profile