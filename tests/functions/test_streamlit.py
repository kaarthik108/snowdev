import os
import yaml
from unittest.mock import MagicMock, patch
import pytest
from snowdev import StreamlitAppDeployer


class TestStreamlitAppDeployer:
    TEMP_DIRECTORY_NAME = "test_deployer_tmp"

    @patch("snowdev.SnowflakeConnection")
    def test_get_connection_details_from_yml(self, MockSnowflakeConnection, tmpdir):
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

        mock_session = MagicMock()
        MockSnowflakeConnection.return_value.get_session.return_value = mock_session

        deployer = StreamlitAppDeployer(mock_session, "test_stage")
        connection_details = deployer.get_connection_details_from_yml(tmpdir)

        assert connection_details == yml_content

    @patch("snowdev.SnowflakeConnection")
    def test_create_stage_if_not_exists(self, MockSnowflakeConnection):
        mock_session = MagicMock()
        MockSnowflakeConnection.return_value.get_session.return_value = mock_session

        deployer = StreamlitAppDeployer(mock_session, "test_stage")
        deployer.create_stage_if_not_exists("test_stage")

        mock_session.sql.assert_called_once()
