from unittest import mock

import pytest

from snowdev import SnowflakeRegister

SNOW_REGISTER = "snowdev.SnowflakeRegister"


@pytest.fixture
def setup_snowflake_register():
    with mock.patch(f"{SNOW_REGISTER}._register_entity") as mock_register, mock.patch(
        f"{SNOW_REGISTER}.get_connection_details_from_toml"
    ) as mock_get_connection:

        mock_get_connection.return_value = {
            "database": "test_db",
            "schema": "test_schema",
            "role": "test_role",
        }

        mock_session = mock.MagicMock()
        mock_session.use_database.return_value = None
        mock_session.use_schema.return_value = None
        mock_session.use_role.return_value = None

        yield SnowflakeRegister(mock_session), mock_register


def test_register_udf(setup_snowflake_register):
    """Test the registration of a UDF."""
    register, mock_register = setup_snowflake_register
    register.main("src/udf/get_sentiment/app.py", "get_sentiment", "snowdev", [], False)
    mock_register.assert_called_with(
        "src/udf/get_sentiment/app.py",
        "get_sentiment",
        "snowdev",
        [],
        None,
        False,
        execute_as="OWNER",
    )


def test_register_sproc(setup_snowflake_register):
    """Test the registration of a Stored Procedure."""
    register, mock_register = setup_snowflake_register
    register.main("src/sproc/test_sproc/app.py", "test_sproc", "snowdev", [], True)
    mock_register.assert_called_with(
        "src/sproc/test_sproc/app.py",
        "test_sproc",
        "snowdev",
        [],
        None,
        True,
        execute_as="caller",
    )
