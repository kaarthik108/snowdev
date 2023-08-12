from snow_functions.SnowConnect import SnowflakeConnection


class snowflakeregister(SnowflakeConnection):

    def __init__(self):
        super().__init__()
        self.session = self.get_session()
        self.is_permanent = True
        self.replace = True

    def register_sproc(self, func, function_name, packages, stage_location, imports):
        self.session.sproc.register_from_file(
            file_path=func,
            func_name="run",
            name=function_name,
            packages=packages,
            imports=imports,
            is_permanent=self.is_permanent,
            stage_location=f"@{stage_location}",
            replace=self.replace,
            execute_as="CALLER",
        )

    def register_udf(self, func, function_name, packages, stage_location, imports):

        self.session.add_packages(*packages)

        self.session.udf.register_from_file(
            file_path=func,
            func_name="run",
            name=function_name,
            is_permanent=self.is_permanent,
            replace=self.replace,
            imports=imports,
            stage_location=f"@{stage_location}",
            packages=packages,
        )

    def main(
        self, func, function_name, stage_location, packages, is_sproc, imports=None
    ):
        if is_sproc:
            self.register_sproc(
                func=func,
                function_name=function_name,
                packages=packages,
                stage_location=stage_location,
                imports=imports,
            )
        else:
            self.register_udf(
                func=func,
                function_name=function_name,
                stage_location=stage_location,
                packages=packages,
                imports=imports,
            )

# SNOW_DEPLOY = snowflakeregister()
