import pandas as pd


def calculate_quality_summary(dataframe: pd.DataFrame) -> dict:
    """
    Calculate an overall data quality summary.
    """

    total_cells = dataframe.shape[0] * dataframe.shape[1]

    missing_cells = int(dataframe.isna().sum().sum())

    duplicate_rows = int(dataframe.duplicated().sum())

    if total_cells > 0:
        completeness_percentage = (
            (total_cells - missing_cells) / total_cells
        ) * 100
    else:
        completeness_percentage = 0.0

    return {
        "total_rows": int(len(dataframe)),
        "total_columns": int(len(dataframe.columns)),
        "total_cells": int(total_cells),
        "missing_cells": missing_cells,
        "duplicate_rows": duplicate_rows,
        "completeness_percentage": round(
            completeness_percentage, 2
        ),
        "quality_status": (
            "PASS"
            if missing_cells == 0 and duplicate_rows == 0
            else "REVIEW"
        ),
    }