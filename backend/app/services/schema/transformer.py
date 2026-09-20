import pandas as pd

from app.services.schema.normalizer import normalize_column_name


def normalize_dataframe_columns(
    dataframe: pd.DataFrame,
) -> pd.DataFrame:
    """
    Return a copy of the dataframe with normalized column names.
    """

    normalized_dataframe = dataframe.copy()

    normalized_dataframe.columns = [
        normalize_column_name(column)
        for column in normalized_dataframe.columns
    ]

    return normalized_dataframe
