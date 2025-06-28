from unittest.mock import patch, MagicMock, call

from app.core.config import settings  # Import settings

# Import the specific operator we need to patch
from sqlalchemy.sql.operators import ColumnOperators

# Assuming models are accessible for column context
from app.db.models.cinema_models import Cinema
from app.tools.statement_builders.movies_statement_builder import _build_cinema_filter

# --- Mock Objects ---
# (Your mock object classes can remain if used elsewhere, but are not strictly necessary for these tests with MagicMock)

# --- Test Cases ---


@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.func")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_cinema_filter_default_wildcard(
    mock_logger,
    mock_sql_func,
    mock_or,
    mocker,
):
    """Test that the default ['*'] input results in no filter (returns None)."""
    result = _build_cinema_filter(["*"])
    assert result is None

    # Ensure func.similarity() and its __gt__ are mocked for completeness,
    # though not expected to be called here.
    if not hasattr(mock_sql_func.similarity, "return_value") or not isinstance(
        mock_sql_func.similarity.return_value, MagicMock
    ):
        mock_sql_func.similarity.return_value = MagicMock()
    if not hasattr(mock_sql_func.similarity.return_value, "__gt__") or not isinstance(
        mock_sql_func.similarity.return_value.__gt__, MagicMock
    ):
        mock_sql_func.similarity.return_value.__gt__ = MagicMock(
            return_value=MagicMock()
        )

    mock_sql_func.similarity.assert_not_called()
    mock_or.assert_not_called()
    mock_logger.info.assert_not_called()


@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.func")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_cinema_filter_empty_list(mock_logger, mock_sql_func, mock_or):
    """Test that an empty list [] input results in no filter (returns None)."""
    result = _build_cinema_filter([])
    assert result is None

    if not hasattr(mock_sql_func.similarity, "return_value") or not isinstance(
        mock_sql_func.similarity.return_value, MagicMock
    ):
        mock_sql_func.similarity.return_value = MagicMock()
    if not hasattr(mock_sql_func.similarity.return_value, "__gt__") or not isinstance(
        mock_sql_func.similarity.return_value.__gt__, MagicMock
    ):
        mock_sql_func.similarity.return_value.__gt__ = MagicMock(
            return_value=MagicMock()
        )

    mock_sql_func.similarity.assert_not_called()
    mock_or.assert_not_called()
    mock_logger.info.assert_not_called()


@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.func")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_cinema_filter_only_wildcards_or_empty_strings(
    mock_logger, mock_sql_func, mock_or, mocker
):
    """Test lists containing only '*' or empty/whitespace strings like '   '."""
    cinemas = ["*", "", "   ", "*"]  # "   " should be processed

    # --- Setup mocks for the "   " case ---
    mock_similarity_condition = MagicMock(name="SimCondForSpaces")
    mock_similarity_call_result = MagicMock(name="SimilarityCallResultForSpaces")
    mock_similarity_call_result.__gt__.return_value = mock_similarity_condition
    mock_sql_func.similarity.return_value = mock_similarity_call_result

    mock_ilike_condition = MagicMock(name="ILikeCondForSpaces")
    mock_ilike_patch = mocker.patch.object(
        ColumnOperators, "ilike", return_value=mock_ilike_condition
    )

    mock_inner_or_result = MagicMock(name="InnerOrForSpaces")
    mock_outer_or_result = MagicMock(name="OuterOrForSpaces")
    mock_or.side_effect = [mock_inner_or_result, mock_outer_or_result]

    # --- Call the function under test ---
    result = _build_cinema_filter(cinemas)

    # --- Assertions ---
    # Assertions for "   " processing
    mock_sql_func.similarity.assert_called_once_with(Cinema.cinema_name, "   ")
    mock_similarity_call_result.__gt__.assert_called_once_with(settings.FUZZY_THRESHOLD)
    mock_ilike_patch.assert_called_once_with("%   %")

    assert mock_or.call_count == 2
    mock_or.assert_has_calls(
        [
            call(mock_similarity_condition, mock_ilike_condition),  # Inner or_
            call(mock_inner_or_result),  # Outer or_
        ],
        any_order=False,
    )

    assert result == mock_outer_or_result
    mock_logger.info.assert_called_once()


@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.func")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_cinema_filter_single_cinema(mock_logger, mock_sql_func, mock_or, mocker):
    """Test with a single valid cinema string."""
    cinema_name = "Cinema Central"
    cinemas = [cinema_name]

    mock_similarity_condition = MagicMock(name="SimilarityCondition")
    mock_ilike_condition = MagicMock(name="ILikeCondition")

    mock_sql_func.similarity.return_value.__gt__.return_value = (
        mock_similarity_condition
    )

    mock_ilike_patch = mocker.patch.object(
        ColumnOperators, "ilike", return_value=mock_ilike_condition
    )

    mock_inner_or = MagicMock(name="InnerOrResult")
    mock_outer_or = MagicMock(name="OuterOrResult")
    mock_or.side_effect = [mock_inner_or, mock_outer_or]

    result = _build_cinema_filter(cinemas)

    mock_sql_func.similarity.assert_called_once_with(Cinema.cinema_name, cinema_name)
    mock_sql_func.similarity.return_value.__gt__.assert_called_once_with(
        settings.FUZZY_THRESHOLD
    )
    mock_ilike_patch.assert_called_once_with(f"%{cinema_name}%")

    assert mock_or.call_count == 2
    mock_or.assert_has_calls(
        [
            call(mock_similarity_condition, mock_ilike_condition),
            call(mock_inner_or),
        ],
        any_order=False,
    )

    assert result == mock_outer_or
    mock_logger.info.assert_called_once()


@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.func")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_cinema_filter_multiple_cinemas(
    mock_logger, mock_sql_func, mock_or, mocker
):
    """Test with multiple valid cinema strings."""
    cinema1 = "Cinema Central"
    cinema2 = "Multiplex West"
    cinemas = [cinema1, cinema2]

    mock_sim_cond1 = MagicMock(name="SimCond1")
    mock_ilike_cond1 = MagicMock(name="ILikeCond1")
    mock_sim_cond2 = MagicMock(name="SimCond2")
    mock_ilike_cond2 = MagicMock(name="ILikeCond2")

    mock_sim_call_result1 = MagicMock(name="SimCallResult1")
    mock_sim_call_result2 = MagicMock(name="SimCallResult2")

    mock_sim_call_result1.__gt__.return_value = mock_sim_cond1
    mock_sim_call_result2.__gt__.return_value = mock_sim_cond2

    mock_sql_func.similarity.side_effect = [
        mock_sim_call_result1,
        mock_sim_call_result2,
    ]

    mock_ilike_patch = mocker.patch.object(
        ColumnOperators, "ilike", side_effect=[mock_ilike_cond1, mock_ilike_cond2]
    )

    mock_inner_or1 = MagicMock(name="InnerOr1")
    mock_inner_or2 = MagicMock(name="InnerOr2")
    mock_outer_or = MagicMock(name="OuterOrResult")
    mock_or.side_effect = [mock_inner_or1, mock_inner_or2, mock_outer_or]

    result = _build_cinema_filter(cinemas)

    assert mock_sql_func.similarity.call_count == 2
    mock_sql_func.similarity.assert_has_calls(
        [
            call(Cinema.cinema_name, cinema1),
            call(Cinema.cinema_name, cinema2),
        ],
        any_order=False,
    )

    mock_sim_call_result1.__gt__.assert_called_once_with(settings.FUZZY_THRESHOLD)
    mock_sim_call_result2.__gt__.assert_called_once_with(settings.FUZZY_THRESHOLD)

    assert mock_ilike_patch.call_count == 2
    mock_ilike_patch.assert_has_calls(
        [call(f"%{cinema1}%"), call(f"%{cinema2}%")], any_order=False
    )

    assert mock_or.call_count == 3
    mock_or.assert_has_calls(
        [
            call(mock_sim_cond1, mock_ilike_cond1),
            call(mock_sim_cond2, mock_ilike_cond2),
            call(mock_inner_or1, mock_inner_or2),
        ],
        any_order=False,
    )

    assert result == mock_outer_or
    mock_logger.info.assert_called_once()


@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.func")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_cinema_filter_mixed_cinemas(mock_logger, mock_sql_func, mock_or, mocker):
    """Test with mixed valid, wildcard, and empty cinemas."""
    cinema1 = "Cinema Central"
    cinema3 = "Plaza"
    cinemas = [cinema1, "*", cinema3, ""]

    mock_sim_cond1 = MagicMock(name="SimCond1Mixed")
    mock_ilike_cond1 = MagicMock(name="ILikeCond1Mixed")
    mock_sim_cond3 = MagicMock(name="SimCond3Mixed")
    mock_ilike_cond3 = MagicMock(name="ILikeCond3Mixed")

    mock_sim_call_result1 = MagicMock(name="SimCallResult1Mixed")
    mock_sim_call_result3 = MagicMock(name="SimCallResult3Mixed")

    mock_sim_call_result1.__gt__.return_value = mock_sim_cond1
    mock_sim_call_result3.__gt__.return_value = mock_sim_cond3

    mock_sql_func.similarity.side_effect = [
        mock_sim_call_result1,
        mock_sim_call_result3,
    ]

    mock_ilike_patch = mocker.patch.object(
        ColumnOperators, "ilike", side_effect=[mock_ilike_cond1, mock_ilike_cond3]
    )

    mock_inner_or1 = MagicMock(name="InnerOr1Mixed")
    mock_inner_or3 = MagicMock(name="InnerOr3Mixed")
    mock_outer_or = MagicMock(name="OuterOrResultMixed")
    mock_or.side_effect = [mock_inner_or1, mock_inner_or3, mock_outer_or]

    result = _build_cinema_filter(cinemas)

    assert mock_sql_func.similarity.call_count == 2
    mock_sql_func.similarity.assert_has_calls(
        [
            call(Cinema.cinema_name, cinema1),
            call(Cinema.cinema_name, cinema3),
        ],
        any_order=False,
    )
    mock_sim_call_result1.__gt__.assert_called_once_with(settings.FUZZY_THRESHOLD)
    mock_sim_call_result3.__gt__.assert_called_once_with(settings.FUZZY_THRESHOLD)

    assert mock_ilike_patch.call_count == 2
    mock_ilike_patch.assert_has_calls(
        [call(f"%{cinema1}%"), call(f"%{cinema3}%")], any_order=False
    )

    assert mock_or.call_count == 3
    mock_or.assert_has_calls(
        [
            call(mock_sim_cond1, mock_ilike_cond1),
            call(mock_sim_cond3, mock_ilike_cond3),
            call(mock_inner_or1, mock_inner_or3),
        ],
        any_order=False,
    )

    assert result == mock_outer_or
    mock_logger.info.assert_called_once()


@patch("app.tools.statement_builders.movies_statement_builder.or_")
@patch("app.tools.statement_builders.movies_statement_builder.func")
@patch("app.tools.statement_builders.movies_statement_builder.logger")
def test_build_cinema_filter_processes_space_only_strings(
    mock_logger, mock_sql_func, mock_or, mocker
):
    """Test that SUT processes non-empty, non-wildcard strings like spaces directly."""
    cinemas = [" ", "   "]

    mock_sim_cond_space1 = MagicMock(name="SimCondSpace1")
    mock_ilike_cond_space1 = MagicMock(name="ILikeCondSpace1")
    mock_sim_cond_space2 = MagicMock(name="SimCondSpace2")
    mock_ilike_cond_space2 = MagicMock(name="ILikeCondSpace2")

    mock_sim_call_result_space1 = MagicMock(name="SimCallResultSpace1")
    mock_sim_call_result_space2 = MagicMock(name="SimCallResultSpace2")

    mock_sim_call_result_space1.__gt__.return_value = mock_sim_cond_space1
    mock_sim_call_result_space2.__gt__.return_value = mock_sim_cond_space2

    mock_sql_func.similarity.side_effect = [
        mock_sim_call_result_space1,
        mock_sim_call_result_space2,
    ]

    mock_ilike_patch = mocker.patch.object(
        ColumnOperators,
        "ilike",
        side_effect=[mock_ilike_cond_space1, mock_ilike_cond_space2],
    )

    mock_inner_or_space1 = MagicMock(name="InnerOrSpace1")
    mock_inner_or_space2 = MagicMock(name="InnerOrSpace2")
    mock_outer_or_result = MagicMock(name="OuterOrResultSpaces")
    mock_or.side_effect = [
        mock_inner_or_space1,
        mock_inner_or_space2,
        mock_outer_or_result,
    ]

    result = _build_cinema_filter(cinemas)

    assert mock_sql_func.similarity.call_count == 2
    mock_sql_func.similarity.assert_has_calls(
        [
            call(Cinema.cinema_name, " "),
            call(Cinema.cinema_name, "   "),
        ],
        any_order=False,
    )

    mock_sim_call_result_space1.__gt__.assert_called_once_with(settings.FUZZY_THRESHOLD)
    mock_sim_call_result_space2.__gt__.assert_called_once_with(settings.FUZZY_THRESHOLD)

    assert mock_ilike_patch.call_count == 2
    mock_ilike_patch.assert_has_calls(
        [
            call("% %"),
            call("%   %"),
        ],
        any_order=False,
    )

    assert mock_or.call_count == 3
    mock_or.assert_has_calls(
        [
            call(mock_sim_cond_space1, mock_ilike_cond_space1),
            call(mock_sim_cond_space2, mock_ilike_cond_space2),
            call(mock_inner_or_space1, mock_inner_or_space2),
        ],
        any_order=False,
    )

    assert result == mock_outer_or_result
    mock_logger.info.assert_called_once()
