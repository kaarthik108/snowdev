from unittest.mock import MagicMock, patch

import pytest
import yaml

from snowdev import StreamlitAppDeployer


@pytest.fixture
def mock_session():
    return MagicMock()


@pytest.fixture
def mock_snowflake_connection(mock_session):
    with patch("snowdev.SnowflakeConnection") as MockSnowflakeConnection:
        MockSnowflakeConnection.return_value.get_session.return_value = mock_session
        yield MockSnowflakeConnection


def test_get_connection_details_from_yml(tmpdir, mock_snowflake_connection):
    yml_content = {
        "connection": {
            "account": "test_account",
            "user": "test_user",
            "password": "test_password",
        }
    }
    yml_path = tmpdir.join("environment.yml")
    with open(yml_path, "w") as file:
        yaml.dump(yml_content, file)

    deployer = StreamlitAppDeployer(mock_snowflake_connection, "test_stage")
    connection_details = deployer.get_connection_details_from_yml(str(tmpdir))

    assert connection_details == yml_content


def test_create_stage_if_not_exists(mock_session):
    deployer = StreamlitAppDeployer(mock_session, "test_stage")
    deployer.create_stage_if_not_exists("test_stage")

    mock_session.sql.assert_called_once_with(
        "CREATE STAGE IF NOT EXISTS test_stage DIRECTORY = (ENABLE = TRUE)"
    )


def test_upload_to_stage(mock_session, tmpdir):
    file_content = "test data"
    file_path = tmpdir.join("test_file.txt")
    with open(file_path, "w") as file:
        file.write(file_content)

    deployer = StreamlitAppDeployer(mock_session, "test_stage")
    deployer.upload_to_stage(str(file_path), "test_stage", "test_app_name")

    mock_session.file.put.assert_called_once_with(
        str(file_path),
        "@test_stage/streamlit/test_app_name",
        auto_compress=False,
        overwrite=True,
    )


def test_apply_connection_details(tmpdir, mock_session):
    yml_content = {
        "database": "test_database",
        "schema": "test_schema",
        "role": "test_role",
    }
    yml_path = tmpdir.join("environment.yml")
    with open(yml_path, "w") as file:
        yaml.dump(yml_content, file)

    deployer = StreamlitAppDeployer(mock_session, "test_stage")
    deployer.apply_connection_details(str(tmpdir))

    mock_session.use_database.assert_called_once_with("test_database")
    mock_session.use_schema.assert_called_once_with("test_schema")
    mock_session.use_role.assert_called_once_with("test_role")
