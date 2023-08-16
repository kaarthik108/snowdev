import unittest
import os
from unittest.mock import patch, MagicMock
from snowdev import main as snowdev_main
from tempfile import TemporaryDirectory


class TestSnowDevCommand(unittest.TestCase):
    def test_init_command(self):
        with TemporaryDirectory() as temp_dir:
            os.chdir(temp_dir)
            args = MagicMock()
            args.command = "init"

            snowdev_main.execute_command(args)

            assert os.path.exists("_src")
            assert os.path.exists("_src/stored_procs")
            assert os.path.exists("_src/streamlit")
            assert os.path.exists("_src/udf")
            assert os.path.exists("_static")
            assert os.path.exists("_static/packages")

    @patch("snowdev.main.DeploymentManager")
    def test_test_command(self, MockDeploymentManager):
        args = MagicMock()
        args.command = "test"
        mock_manager = MockDeploymentManager.return_value

        snowdev_main.execute_command(args)

        mock_manager.test_locally.assert_called_once()

    @patch("snowdev.main.DeploymentManager")
    def test_deploy_command(self, MockDeploymentManager):
        args = MagicMock()
        args.command = "deploy"
        mock_manager = MockDeploymentManager.return_value

        snowdev_main.execute_command(args)

        mock_manager.main.assert_called_once()


if __name__ == "__main__":
    unittest.main()
