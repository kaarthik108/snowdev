from __future__ import annotations

import os
import re

from termcolor import colored


class TaskDeployer:
    def __init__(self, session, stage_name: str):
        self.session = session
        self.stage_name = stage_name
        self.warehouse = self.session.get_current_warehouse().replace('"', "")
        self.database = self.session.get_current_database().replace('"', "")

    def create_stage_if_not_exists(self, stage_name: str):
        self.session.sql(
            f"CREATE STAGE IF NOT EXISTS {stage_name} DIRECTORY = (ENABLE = TRUE)"
        ).collect()

    def deploy_task(self, task_name: str, option: None):
        # Validate the task name
        if not re.match("^[a-zA-Z0-9_]+$", task_name):
            print(
                colored(
                    f"⚠️ Invalid task name {task_name}! Task names should only contain alphanumeric characters and underscores.",
                    "yellow",
                )
            )
            return

        # Define the path to the SQL file
        sql_file_path = os.path.join("src", "task", task_name, "app.sql")

        # Check if the SQL file exists
        if not os.path.exists(sql_file_path):
            print(colored(f"⚠️ SQL file {sql_file_path} does not exist!", "yellow"))
            return

        if option:
            statement = (
                f"EXECUTE TASK {task_name}"
                if option == "execute"
                else f"ALTER TASK {task_name} {option}"
            )
            self.session.sql(statement).collect()
            print(colored(f"✅ Task {task_name} {option} successfully!", "green"))
            return

        try:
            # Read the content of the SQL file
            with open(sql_file_path, "r") as sql_file:
                sql_content = sql_file.read()

            statements = [
                stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
            ]

            if statements:
                for statement in statements:
                    self.session.sql(statement).collect()
                    print(
                        colored(f"✅ Task {task_name} deployed successfully!", "green")
                    )
            else:
                print(colored(f"⚠️ SQL file {sql_file_path} is empty!", "yellow"))

        except Exception as e:
            print(
                colored(
                    f"⚠️ An error occurred while deploying the task {task_name}: {str(e)}",
                    "red",
                )
            )
