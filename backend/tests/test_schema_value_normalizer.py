from app.services.schema.value_normalizer import (
    normalize_text_value,
    normalize_numeric_value,
    normalize_date_value,
)


def test_normalize_text_value():
    assert normalize_text_value("  Rahul Kumar  ") == "rahul kumar"


def test_normalize_text_value_missing_marker():
    assert normalize_text_value(" NULL ") is None


def test_normalize_text_value_non_string():
    assert normalize_text_value(12500) == 12500


def test_normalize_numeric_value_from_integer():
    assert str(normalize_numeric_value(12500)) == "12500"


def test_normalize_numeric_value_from_formatted_string():
    assert str(normalize_numeric_value(" 12,500 ")) == "12500"


def test_normalize_numeric_value_invalid_string():
    assert normalize_numeric_value("hello") == "hello"


def test_normalize_numeric_value_missing_marker():
    assert normalize_numeric_value("N/A") is None


def test_normalize_date_value_iso():
    assert normalize_date_value("2026-08-01") == "2026-08-01"


def test_normalize_date_value_other_format():
    assert normalize_date_value("08/01/2026") == "2026-08-01"


def test_normalize_date_value_missing_marker():
    assert normalize_date_value("NULL") is None
def test_numeric_nan_is_missing():
    import math

    from app.services.schema.value_normalizer import normalize_numeric_value

    result = normalize_numeric_value(float("nan"))

    assert result is None


def test_boolean_values_are_not_converted():
    from app.services.schema.value_normalizer import normalize_numeric_value

    assert normalize_numeric_value(True) is True
    assert normalize_numeric_value(False) is False
