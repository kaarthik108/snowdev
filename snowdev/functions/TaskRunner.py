import yaml

from . import SnowflakeConnection


class TaskRunner(SnowflakeConnection):
    def __init__(self, task_name):
        super().__init__()
        self.session = self.get_session()
        self.task_name = task_name
        self.yml_path = "src/tasks/tasks.yml"
        self.config = self._load_yml()
        (
            self.function_name,
            self.full_task_name,
        ) = self._get_function_and_full_task_name()

    def _load_yml(self):
        with open(self.yml_path, "r") as file:
            return yaml.safe_load(file)

    def _get_function_and_full_task_name(self):
        task_config = next(
            (item for item in self.config if item["name"] == self.task_name),
            None,
        )
        if not task_config:
            raise ValueError(f"Task {self.task_name} not found in YAML file")
        function_name = task_config.get("function_name", "")
        full_task_name = (
            f"{task_config.get('function', '')}_{self.task_name}"
            if task_config.get("function", "")
            else self.task_name
        )
        return function_name, full_task_name

    def create_task_sql(self):
        task_config = next(
            (item for item in self.config if item["name"] == self.task_name),
            None,
        )
        if not task_config:
            raise ValueError(f"Task {self.task_name} not found in YAML file")

        # Extract details from the YAML configuration
        name = self.full_task_name
        warehouse = task_config["config"]["warehouse"]
        schedule = task_config["schedule"]["cron"]
        db = task_config["config"]["db"]
        function_name = self.function_name

        # Extract and format the arguments for the CALL statement
        args_dict = task_config["config"].get("args", {})
        args = []
        for key, value in args_dict.items():
            if isinstance(value, str):
                args.append(f"'{value}'")
            elif isinstance(value, list):
                args.append(f"'{' '.join(value)}'")
            elif isinstance(value, bool):
                args.append(str(value).upper())
            else:
                args.append(str(value))
        formatted_args = ", ".join(args)

        # Create the SQL string using the details
        sql = (
            f"CREATE OR REPLACE TASK analytics.public.{name}\n"
            f"    WAREHOUSE = '{warehouse}'\n"
            f"    SCHEDULE  = 'using CRON {schedule}'\n"
            f"    ALLOW_OVERLAPPING_EXECUTION = TRUE\n"
            f"AS\n"
            f"   CALL {db}.public.{function_name}({formatted_args});"
        )
        return sql

    def handler_task(self):
        task_sql = self.create_task_sql()
        print(f"Running task {self.task_name} with SQL: {task_sql}")
        try:
            if self.session.get_current_database() == "ANALYTICS":
                self.session.sql(task_sql).collect()
                self.session.sql(f"ALTER TASK {self.full_task_name} RESUME").collect()
            else:
                print(
                    f" You are not authorized to run tasks in {self.session.get_current_database()} database"
                )
        except Exception as e:
            print(f"Error running task {self.task_name}: {e}")
