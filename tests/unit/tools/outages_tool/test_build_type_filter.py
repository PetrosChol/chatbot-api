# Assuming Outage model is needed for ColumnElement context, though not directly used by _build_outage_type_filter logic itself
# If not strictly needed, this import could be removed.
from app.db.models.outage_model import Outage

# Function under test
from app.tools.statement_builders.outages_statement_builder import (
    _build_outage_type_filter,
)

# --- Mock Objects (Similar to test_build_fuzzy_conditions.py) ---


# Mock the SQLAlchemy comparison object returned by build_fuzzy_conditions
class MockSQLAlchemyComparison:
    def __init__(self, value):
        self.value = value  # Store the value for assertion

    def __eq__(self, other):
        return isinstance(other, MockSQLAlchemyComparison) and self.value == other.value

    def __repr__(self):
        return f"MockSQLAlchemyComparison({self.value})"


# --- Test Cases ---


def test_build_outage_type_filter_none_input():
    """Test that None input results in no filter (returns None)."""
    result = _build_outage_type_filter(None)
    assert result is None


def test_build_outage_type_filter_wildcard_input():
    """Test that '*' input results in no filter (returns None)."""
    result = _build_outage_type_filter("*")
    assert result is None


def test_build_outage_type_filter_empty_string_input():
    """Test that an empty string input results in no filter (returns None)."""
    result = _build_outage_type_filter("")
    assert result is None


def test_build_outage_type_filter_valid_type():
    """Test with a valid type string, expects an exact match condition."""
    outage_type = "power"
    result = _build_outage_type_filter(outage_type)

    assert result is not None
    # Check if the generated condition is an equality comparison
    # and if the left side is the Outage.outage_type column
    # and the right side is the provided outage_type string.
    assert result.left.name == Outage.outage_type.key  # Compare column names
    assert result.right.value == outage_type
    assert result.operator.__name__ == "eq"  # Check for equality operator


def test_build_outage_type_filter_valid_type_greek():
    """Test with a valid Greek type string, expects an exact match condition."""
    outage_type = "νερό"  # Greek for water
    result = _build_outage_type_filter(outage_type)

    assert result is not None
    assert result.left.name == Outage.outage_type.key
    assert result.right.value == outage_type
    assert result.operator.__name__ == "eq"
