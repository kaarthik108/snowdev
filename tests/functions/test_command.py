import os
from tempfile import TemporaryDirectory
from unittest.mock import MagicMock, patch

import pytest

from snowdev import main as snowdev_main


@pytest.fixture
def setup_args():
    return MagicMock()


@pytest.fixture
def temp_dir():
    with TemporaryDirectory() as tmp:
        yield tmp


def test_execute_init_command_creates_expected_directories(setup_args, temp_dir):
    """Test that the init command creates the expected directory structure."""
    os.chdir(temp_dir)
    setup_args.command = "init"
    snowdev_main.execute_command(setup_args)

    expected_dirs = [
        "_src",
        "_src/sproc",
        "_src/streamlit",
        "_src/udf",
        "_static",
        "_static/packages",
    ]

    for dir in expected_dirs:
        assert os.path.exists(dir), f"Expected directory '{dir}' not found."


@patch("snowdev.main.DeploymentManager")
def test_execute_test_command_calls_test_locally(MockDeploymentManager, setup_args):
    """Test that the test command invokes the test_locally method of DeploymentManager."""
    setup_args.command = "test"
    mock_manager = MockDeploymentManager.return_value
    snowdev_main.execute_command(setup_args)
    mock_manager.test_locally.assert_called_once()


@patch("snowdev.main.DeploymentManager")
def test_execute_deploy_command_calls_main_method(MockDeploymentManager, setup_args):
    """Test that the deploy command invokes the main method of DeploymentManager."""
    setup_args.command = "deploy"
    mock_manager = MockDeploymentManager.return_value
    snowdev_main.execute_command(setup_args)
    mock_manager.main.assert_called_once()
