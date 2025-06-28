from unittest.mock import patch, MagicMock, call

from app.core.config import settings  # Import settings

# Assuming models are accessible for column context
from app.db.models.cinema_models import Movie
from app.tools.statement_builders.movies_statement_builder import _build_movie_filter

# --- Mock Objects ---


# Mock the SQLAlchemy condition object returned by build_fuzzy_conditions
class MockSQLAlchemyFuzzyCondition:
    def __init__(self, value):
        self.value = value  # Store the value for assertion

    def __eq__(self, other):
        return (
            isinstance(other, MockSQLAlchemyFuzzyCondition)
            and self.value == other.value
        )

    def __repr__(self):
        return f"MockSQLAlchemyFuzzyCondition({self.value})"


# --- Test Cases ---


@patch("app.tools.statement_builders.movies_statement_builder.build_fuzzy_conditions")
@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_movie_filter_default_wildcard(mock_logger, mock_or, mock_build_fuzzy):
    """Test that the default ['*'] input results in no filter (returns None)."""
    result = _build_movie_filter(["*"])
    assert result is None
    mock_build_fuzzy.assert_not_called()
    mock_or.assert_not_called()
    mock_logger.info.assert_not_called()


@patch(
    "app.tools.statement_builders.movies_statement_builder.build_fuzzy_conditions",
    return_value=[],
)
@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_movie_filter_empty_list(mock_logger, mock_or, mock_build_fuzzy):
    """Test that an empty list [] input calls build_fuzzy but returns None."""
    result = _build_movie_filter([])
    assert result is None
    # build_fuzzy_conditions should be called for each normalized field
    expected_calls = [
        call(Movie.normalized_movie_name, [], threshold=settings.FUZZY_THRESHOLD),
        call(Movie.normalized_movie_name_greek, [], threshold=settings.FUZZY_THRESHOLD),
        call(
            Movie.normalized_movie_name_english, [], threshold=settings.FUZZY_THRESHOLD
        ),
    ]
    mock_build_fuzzy.assert_has_calls(expected_calls, any_order=True)
    assert mock_build_fuzzy.call_count == 3
    mock_or.assert_not_called()  # No conditions to OR
    mock_logger.info.assert_not_called()


@patch(
    "app.tools.statement_builders.movies_statement_builder.build_fuzzy_conditions",
    return_value=[],
)
@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_movie_filter_only_wildcards_or_empty_strings(
    mock_logger, mock_or, mock_build_fuzzy
):
    """Test lists containing only '*' or empty strings, assuming build_fuzzy handles them."""
    movies = ["*", "", "   ", "*"]
    result = _build_movie_filter(movies)
    assert result is None
    # Expect build_fuzzy_conditions to be called for each normalized field
    expected_calls = [
        call(Movie.normalized_movie_name, movies, threshold=settings.FUZZY_THRESHOLD),
        call(
            Movie.normalized_movie_name_greek,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
        call(
            Movie.normalized_movie_name_english,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
    ]
    mock_build_fuzzy.assert_has_calls(expected_calls, any_order=True)
    assert mock_build_fuzzy.call_count == 3
    # Since build_fuzzy_conditions returns [], or_ should not be called
    mock_or.assert_not_called()
    mock_logger.info.assert_not_called()


@patch("app.tools.statement_builders.movies_statement_builder.build_fuzzy_conditions")
@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_movie_filter_single_movie(mock_logger, mock_or, mock_build_fuzzy):
    """Test with a single valid movie string using fuzzy matching."""
    mock_condition_primary = MockSQLAlchemyFuzzyCondition("fuzzy_for_primary_movie1")
    # Simulate that only the primary normalized name matches
    mock_build_fuzzy.side_effect = [
        [mock_condition_primary],  # For normalized_movie_name
        [],  # For normalized_movie_name_greek
        [],  # For normalized_movie_name_english
    ]

    movies = ["Movie Title 1"]
    result = _build_movie_filter(movies)

    expected_calls = [
        call(Movie.normalized_movie_name, movies, threshold=settings.FUZZY_THRESHOLD),
        call(
            Movie.normalized_movie_name_greek,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
        call(
            Movie.normalized_movie_name_english,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
    ]
    mock_build_fuzzy.assert_has_calls(expected_calls, any_order=True)
    assert mock_build_fuzzy.call_count == 3
    # or_ should be called with the single condition from the primary match
    mock_or.assert_called_once_with(mock_condition_primary)
    assert result == mock_or.return_value
    mock_logger.info.assert_called_once_with(
        "Applying fuzzy movie name filter conditions using primary, Greek, and English normalized columns."
    )


@patch("app.tools.statement_builders.movies_statement_builder.build_fuzzy_conditions")
@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_movie_filter_multiple_movies(mock_logger, mock_or, mock_build_fuzzy):
    """Test with multiple valid movie strings using fuzzy matching, expects or_()."""
    mock_cond_primary1 = MockSQLAlchemyFuzzyCondition("fuzzy_primary_movie1")
    mock_cond_greek2 = MockSQLAlchemyFuzzyCondition("fuzzy_greek_movie2")
    # Simulate matches on different fields for different terms if needed, or just one field
    mock_build_fuzzy.side_effect = [
        [mock_cond_primary1],  # For normalized_movie_name
        [mock_cond_greek2],  # For normalized_movie_name_greek
        [],  # For normalized_movie_name_english
    ]

    mock_or_result = MagicMock(name="or_result")
    mock_or.return_value = mock_or_result

    movies = ["Movie Title 1", "Second Movie"]
    result = _build_movie_filter(movies)

    expected_calls = [
        call(Movie.normalized_movie_name, movies, threshold=settings.FUZZY_THRESHOLD),
        call(
            Movie.normalized_movie_name_greek,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
        call(
            Movie.normalized_movie_name_english,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
    ]
    mock_build_fuzzy.assert_has_calls(expected_calls, any_order=True)
    assert mock_build_fuzzy.call_count == 3
    # Expect or_ to be called with all collected conditions
    mock_or.assert_called_once_with(mock_cond_primary1, mock_cond_greek2)
    assert result == mock_or_result
    mock_logger.info.assert_called_once_with(
        "Applying fuzzy movie name filter conditions using primary, Greek, and English normalized columns."
    )


@patch("app.tools.statement_builders.movies_statement_builder.build_fuzzy_conditions")
@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_movie_filter_mixed_movies(mock_logger, mock_or, mock_build_fuzzy):
    """Test with mixed valid, wildcard, and empty movies using fuzzy matching."""
    mock_cond_primary1 = MockSQLAlchemyFuzzyCondition("fuzzy_primary_movie1")
    mock_cond_english3 = MockSQLAlchemyFuzzyCondition("fuzzy_english_movie3")
    # Simulate build_fuzzy_conditions filtering out '*' and '' and returning only valid conditions
    # for the relevant fields.
    mock_build_fuzzy.side_effect = [
        [mock_cond_primary1],  # For normalized_movie_name
        [],  # For normalized_movie_name_greek
        [mock_cond_english3],  # For normalized_movie_name_english
    ]

    mock_or_result = MagicMock(name="or_result_mixed")
    mock_or.return_value = mock_or_result

    movies = ["Movie Title 1", "*", "Third Movie", ""]
    result = _build_movie_filter(movies)

    expected_calls = [
        call(Movie.normalized_movie_name, movies, threshold=settings.FUZZY_THRESHOLD),
        call(
            Movie.normalized_movie_name_greek,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
        call(
            Movie.normalized_movie_name_english,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
    ]
    mock_build_fuzzy.assert_has_calls(expected_calls, any_order=True)
    assert mock_build_fuzzy.call_count == 3
    # Expect or_ to be called with the two valid conditions
    mock_or.assert_called_once_with(mock_cond_primary1, mock_cond_english3)
    assert result == mock_or_result
    mock_logger.info.assert_called_once_with(
        "Applying fuzzy movie name filter conditions using primary, Greek, and English normalized columns."
    )


@patch(
    "app.tools.statement_builders.movies_statement_builder.build_fuzzy_conditions",
    return_value=[],
)
@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_movie_filter_no_conditions_returned(
    mock_logger, mock_or, mock_build_fuzzy
):
    """Test when build_fuzzy_conditions returns an empty list."""
    movies = ["NonMatchingMovie"]
    # Simulate build_fuzzy_conditions returning empty lists for all fields
    mock_build_fuzzy.side_effect = [[], [], []]
    result = _build_movie_filter(movies)

    expected_calls = [
        call(Movie.normalized_movie_name, movies, threshold=settings.FUZZY_THRESHOLD),
        call(
            Movie.normalized_movie_name_greek,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
        call(
            Movie.normalized_movie_name_english,
            movies,
            threshold=settings.FUZZY_THRESHOLD,
        ),
    ]
    mock_build_fuzzy.assert_has_calls(expected_calls, any_order=True)
    assert mock_build_fuzzy.call_count == 3
    mock_or.assert_not_called()
    assert result is None  # Should return None if the conditions list is empty
    mock_logger.info.assert_not_called()  # No "Applying..." log if no conditions
