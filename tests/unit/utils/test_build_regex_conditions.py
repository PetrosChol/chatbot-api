from unittest.mock import patch

# Import the function to test - adjust the import path as needed
from app.utils.build_regex_conditions import build_regex_conditions


class MockColumn:
    """Mock for a database column that can be used with operators."""

    def __init__(self, name):
        self.name = name

    def op(self, operator):
        """Mock the op method that returns a function."""

        def apply_operator(pattern):
            """Return a mock condition that stores the pattern for verification."""
            return MockCondition(self.name, operator, pattern)

        return apply_operator


class MockCondition:
    """Mock for a database condition that stores the column, operator and pattern."""

    def __init__(self, column_name, operator, pattern):
        self.column_name = column_name
        self.operator = operator
        self.pattern = pattern

    def __eq__(self, other):
        """Implement equality to check if two conditions are the same."""
        if not isinstance(other, MockCondition):
            return False
        return (
            self.column_name == other.column_name
            and self.operator == other.operator
            and self.pattern == other.pattern
        )

    def __repr__(self):
        """String representation for better debug output."""
        return f"MockCondition({self.column_name}, {self.operator}, {self.pattern})"


# No longer needed as a fixture, patch applied directly in the relevant test


def test_build_regex_conditions_empty_list():
    """Test with empty list returns empty conditions."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(column, [])
    assert conditions == []


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_asterisk_only(mock_norm):
    """Test with only asterisk returns empty conditions."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(column, ["*"])
    assert conditions == []


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_empty_strings(mock_norm):
    """Test with empty strings returns empty conditions."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(column, ["", "", ""])
    assert conditions == []


# Patch where normalize_text is looked up (within build_regex_conditions module)
@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: None if x == "invalid" else x.lower(),
)
def test_build_regex_conditions_none_values(mock_norm):
    """Test with None values (which normalize_text might return for certain inputs)."""
    column = MockColumn("test_column")

    # Call the function with the mock active
    conditions = build_regex_conditions(column, ["valid", "invalid", "also_valid"])

    # Only two valid patterns should be processed ("invalid" should be filtered)
    assert len(conditions) == 2

    # Check the patterns
    # The pattern now includes word boundaries, e.g., r"\mvalid\M"
    expected_patterns = [
        MockCondition("test_column", "~*", r"\mvalid\M"),
        MockCondition("test_column", "~*", r"\malso_valid\M"),
    ]

    # Using set comparison for order-insensitivity if needed, though order should be preserved
    assert len(conditions) == len(expected_patterns)
    for expected_pattern in expected_patterns:
        assert any(
            condition == expected_pattern for condition in conditions
        ), f"Expected pattern {expected_pattern} not found in {conditions}"


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_single_word(mock_norm):
    """Test with single words."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(column, ["apple", "banana", "cherry"])

    expected_patterns = [
        MockCondition("test_column", "~*", r"\mapple\M"),
        MockCondition("test_column", "~*", r"\mbanana\M"),
        MockCondition("test_column", "~*", r"\mcherry\M"),
    ]

    assert len(conditions) == len(expected_patterns)
    for expected_pattern in expected_patterns:
        assert any(
            condition == expected_pattern for condition in conditions
        ), f"Expected pattern {expected_pattern} not found in {conditions}"


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_multiple_words(mock_norm):
    """Test with multiple words that get joined with .*"""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(column, ["red apple", "green banana"])

    expected_patterns = [
        MockCondition("test_column", "~*", r"\mred\M.*\mapple\M"),
        MockCondition("test_column", "~*", r"\mgreen\M.*\mbanana\M"),
    ]

    assert len(conditions) == len(expected_patterns)
    for expected_pattern in expected_patterns:
        assert any(
            condition == expected_pattern for condition in conditions
        ), f"Expected pattern {expected_pattern} not found in {conditions}"


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_special_characters(mock_norm):
    """Test with special characters that should be cleaned and escaped."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(
        column, ["apple+orange", "banana.cherry", "grape(fruit)"]
    )

    # Special characters should be escaped in the regex pattern
    expected_patterns = [
        MockCondition("test_column", "~*", r"\mapple\+orange\M"),  # + is escaped
        MockCondition("test_column", "~*", r"\mbanana\.cherry\M"),  # . is escaped
        MockCondition(
            "test_column", "~*", r"\mgrape\(fruit\)\M"
        ),  # ( and ) are escaped
    ]

    assert len(conditions) == len(expected_patterns)
    for expected_pattern in expected_patterns:
        assert any(
            condition == expected_pattern for condition in conditions
        ), f"Expected pattern {expected_pattern} not found in {conditions}"


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_case_insensitive(mock_norm):
    """Test case insensitivity is preserved by using ~* operator."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(column, ["APPLE", "Banana", "cherry"])

    # All should be lowercase after normalize_text and have word boundaries
    expected_patterns = [
        MockCondition("test_column", "~*", r"\mapple\M"),
        MockCondition("test_column", "~*", r"\mbanana\M"),
        MockCondition("test_column", "~*", r"\mcherry\M"),
    ]

    assert len(conditions) == len(expected_patterns)
    for expected_pattern in expected_patterns:
        assert any(
            condition == expected_pattern for condition in conditions
        ), f"Expected pattern {expected_pattern} not found in {conditions}"


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_regex_escaping(mock_norm):
    """Test that regex special characters are properly escaped."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(
        column, ["apple.pie", "banana?split", "cherry+jubilee"]
    )

    # Special regex characters should be escaped
    expected_patterns = [
        MockCondition("test_column", "~*", r"\mapple\.pie\M"),
        MockCondition("test_column", "~*", r"\mbanana\?split\M"),
        MockCondition("test_column", "~*", r"\mcherry\+jubilee\M"),
    ]

    assert len(conditions) == len(expected_patterns)
    for expected_pattern in expected_patterns:
        assert any(
            condition == expected_pattern for condition in conditions
        ), f"Expected pattern {expected_pattern} not found in {conditions}"


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_mixed_valid_invalid(mock_norm):
    """Test with mix of valid terms, empty strings, and asterisks."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(column, ["apple", "", "*", "banana", "*", ""])

    expected_patterns = [
        MockCondition("test_column", "~*", r"\mapple\M"),
        MockCondition("test_column", "~*", r"\mbanana\M"),
    ]

    assert len(conditions) == len(expected_patterns)
    for expected_pattern in expected_patterns:
        assert any(
            condition == expected_pattern for condition in conditions
        ), f"Expected pattern {expected_pattern} not found in {conditions}"


@patch(
    "app.utils.build_regex_conditions.normalize_text",
    side_effect=lambda x: x.lower() if x else None,
)
def test_build_regex_conditions_real_regex_patterns(mock_norm):
    """Test with complex phrases requiring regex construction."""
    column = MockColumn("test_column")
    conditions = build_regex_conditions(
        column, ["red delicious apple", "green seedless grape"]
    )

    expected_patterns = [
        MockCondition("test_column", "~*", r"\mred\M.*\mdelicious\M.*\mapple\M"),
        MockCondition("test_column", "~*", r"\mgreen\M.*\mseedless\M.*\mgrape\M"),
    ]

    assert len(conditions) == len(expected_patterns)
    for expected_pattern in expected_patterns:
        assert any(
            condition == expected_pattern for condition in conditions
        ), f"Expected pattern {expected_pattern} not found in {conditions}"
