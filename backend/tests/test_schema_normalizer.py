from app.services.schema.normalizer import normalize_column_name


def test_normalize_column_name_with_spaces():
    assert normalize_column_name("Customer ID") == "customer_id"


def test_normalize_column_name_with_camel_case():
    assert normalize_column_name("customerId") == "customer_id"


def test_normalize_column_name_with_hyphen():
    assert normalize_column_name("CUSTOMER-ID") == "customer_id"


def test_normalize_column_name_with_lowercase_spaces():
    assert normalize_column_name("customer name") == "customer_name"


def test_normalize_column_name_with_extra_spaces():
    assert normalize_column_name("  Customer Name  ") == "customer_name"


def test_normalize_column_name_with_repeated_underscores():
    assert normalize_column_name("customer__name") == "customer_name"


def test_normalize_column_name_with_invalid_type():
    try:
        normalize_column_name(123)
        assert False
    except TypeError:
        assert True


def test_normalize_column_name_empty_result():
    try:
        normalize_column_name("---")
        assert False
    except ValueError:
        assert True