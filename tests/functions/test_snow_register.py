from unittest import mock
from snowdev import SnowflakeRegister

SNOW_REGISTER = "snowdev.SnowflakeRegister"


@mock.patch(f"{SNOW_REGISTER}._register_entity")
@mock.patch(f"{SNOW_REGISTER}.get_connection_details_from_toml")
def test_udf_registration(mock_get_connection, mock_register):
    mock_get_connection.return_value = {
        "database": "test_db",
        "schema": "test_schema",
        "role": "test_role",
    }

    mock_session = mock.MagicMock()
    mock_session.use_database.return_value = None
    mock_session.use_schema.return_value = None
    mock_session.use_role.return_value = None

    register = SnowflakeRegister(mock_session)
    register.main("src/udf/get_sentiment/app.py", "get_sentiment", "snowdev", [], False)
    mock_register.assert_called_with(
        "src/udf/get_sentiment/app.py", "get_sentiment", "snowdev", [], None, False
    )


@mock.patch(f"{SNOW_REGISTER}._register_entity")
@mock.patch(f"{SNOW_REGISTER}.get_connection_details_from_toml")
def test_sproc_registration(mock_get_connection, mock_register):
    mock_get_connection.return_value = {
        "database": "test_db",
        "schema": "test_schema",
        "role": "test_role",
    }

    mock_session = mock.MagicMock()
    mock_session.use_database.return_value = None
    mock_session.use_schema.return_value = None
    mock_session.use_role.return_value = None

    register = SnowflakeRegister(mock_session)
    register.main(
        "src/stored_procs/sproc_name/app.py", "sproc_name", "snowdev", [], True
    )
    mock_register.assert_called_with(
        "src/stored_procs/sproc_name/app.py", "sproc_name", "snowdev", [], None, True
    )
