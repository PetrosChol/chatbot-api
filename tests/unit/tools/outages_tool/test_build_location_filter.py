from app.tools.statement_builders.outages_statement_builder import (
    _build_outage_location_filter,
)

# --- Tests for the current behavior of _build_outage_location_filter ---
# The function is currently stubbed to `return None`.


def test_empty_locations_list_returns_none():
    """
    Test that _build_outage_location_filter returns None if the locations list is empty.
    This aligns with the expectation that no filter should be applied.
    """
    result = _build_outage_location_filter(locations=[])
    assert result is None, "Should return None for an empty list of locations."


def test_wildcard_only_locations_list_returns_none():
    """
    Test that _build_outage_location_filter returns None if the locations list contains only '*'.
    The wildcard '*' signifies no specific location filter.
    """
    result = _build_outage_location_filter(locations=["*"])
    assert (
        result is None
    ), "Should return None for a list containing only the wildcard '*'."


def test_empty_or_whitespace_string_locations_list_returns_none():
    """
    Test that _build_outage_location_filter returns None if the locations list contains
    only empty or whitespace strings. These should be treated as no filter.
    (Current stub returns None for any input; this test is consistent with that
     and the likely future intent to ignore such strings).
    """
    result = _build_outage_location_filter(locations=["", "   ", "\t"])
    assert (
        result is None
    ), "Should return None for lists with only empty/whitespace strings."


def test_single_valid_location_string_returns_none_currently():
    """
    Test that _build_outage_location_filter currently returns None even for a valid location string,
    as the filtering logic is not yet implemented.
    """
    result = _build_outage_location_filter(locations=["Springfield"])
    assert result is None, "Currently returns None as the function is stubbed."


def test_multiple_valid_location_strings_returns_none_currently():
    """
    Test that _build_outage_location_filter currently returns None for multiple valid location strings.
    """
    result = _build_outage_location_filter(locations=["Springfield", "Shelbyville"])
    assert result is None, "Currently returns None as the function is stubbed."


def test_mixed_locations_list_with_wildcard_and_empty_returns_none_currently():
    """
    Test that _build_outage_location_filter currently returns None for a mixed list
    containing valid locations, wildcards, and empty strings.
    Future behavior would be to process valid locations and ignore others.
    """
    result = _build_outage_location_filter(
        locations=["Springfield", "*", "", "Shelbyville", "  "]
    )
    assert result is None, "Currently returns None as the function is stubbed."
