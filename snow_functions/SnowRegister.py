from snow_functions.SnowConnect import SnowflakeConnection


class snowflakeregister(SnowflakeConnection):
    def __init__(self):
        super().__init__()
        self.session = self.get_session()

    def function_exists(self, function_name):
        try:
            result = self.session.sql(f"SHOW USER FUNCTIONS LIKE '{function_name}'").collect()
            return len(result) > 0
        except:
            return False

    def get_function_signature(self, function_name):
        try:
            result = self.session.sql(f"SHOW USER FUNCTIONS LIKE '{function_name}'").collect()
            print(result)
            if result:
                signature = result[0]['arguments']
                
                # Split on '(' and ')' and take the second element after splitting on ' '
                arg_types = signature.split("(")[1].split(")")[0].split()[0]
                
                return arg_types.strip()
            return None
        except:
            return None


    def rename_function(self, old_name, new_name, arg_type):
        sql = f"ALTER FUNCTION {old_name}({arg_type}) RENAME TO {new_name}"
        print(sql)
        self.session.sql(sql).collect()

    def drop_function(self, function_name, arg_type):
        sql = f"DROP FUNCTION {function_name}({arg_type})"
        print(sql)
        self.session.sql(sql).collect()


    def register_sproc(self, func, function_name, packages, stage_location, imports, is_temp=False):
        replace = not is_temp
        is_permanent = not is_temp

        self.session.sproc.register_from_file(
            file_path=func,
            func_name="handler",
            name=function_name,
            packages=packages,
            imports=imports,
            is_permanent=is_permanent,
            stage_location=f"@{stage_location}/sproc",
            replace=replace,
            execute_as="CALLER",
            strict=True,
        )

    def register_udf(self, func, function_name, packages, stage_location, imports, is_temp=False):
        replace = not is_temp
        is_permanent = not is_temp

        self.session.add_packages(*packages)
        if imports:
            self.session.add_import(*imports)

        self.session.udf.register_from_file(
            file_path=func,
            func_name="handler",
            name=function_name,
            is_permanent=is_permanent,
            replace=replace,
            imports=imports,
            stage_location=f"@{stage_location}/udf",
            packages=packages,
            source_code_display=True,
        )

    def main(self, func, function_name, stage_location, packages, is_sproc, imports=None):
        # First, try to register the function with a temp_ prefix without replacing
        temp_function_name = "temp_" + function_name
        try:
            if is_sproc:
                self.register_sproc(
                    func=func,
                    function_name=temp_function_name,
                    packages=packages,
                    stage_location=stage_location,
                    imports=imports
                )
            else:
                self.register_udf(
                    func=func,
                    function_name=temp_function_name,
                    stage_location=stage_location,
                    packages=packages,
                    imports=imports
                )

            print(f"Function {temp_function_name} passed the test. Proceeding with deployment...")

            # Fetch the argument type from the temp_ function
            temp_arg_type = self.get_function_signature(temp_function_name)

            # Deploy the function with the original name, replacing any existing ones
            if is_sproc:
                self.register_sproc(
                    func=func,
                    function_name=function_name,
                    packages=packages,
                    stage_location=stage_location,
                    imports=imports
                )
            else:
                self.register_udf(
                    func=func,
                    function_name=function_name,
                    stage_location=stage_location,
                    packages=packages,
                    imports=imports
                )

            # Drop the temp_ function
            if self.function_exists(temp_function_name):
                self.drop_function(temp_function_name, temp_arg_type)

            print(f"Function {function_name} deployed successfully!")

        except Exception as e:
            # If there was an error, drop the temp_ function
            if self.function_exists(temp_function_name):
                print(f"Error occurred. Dropping {temp_function_name}")
                self.drop_function(temp_function_name, temp_arg_type)
            raise e