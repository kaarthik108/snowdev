from termcolor import colored


class snowflakeregister:
    def __init__(self, session):
        self.session = session

    def _entity_exists(self, entity_name, entity_type):
        try:
            result = self.session.sql(
                f"SHOW {entity_type} LIKE '{entity_name}'"
            ).collect()
            return len(result) > 0
        except:
            print(f"Failed to check if {entity_type} {entity_name} exists.")
            return False

    def _get_entity_signature(self, entity_name, entity_type):
        try:
            result = self.session.sql(
                f"SHOW {entity_type} LIKE '{entity_name}'"
            ).collect()
            if result:
                signature = result[0]["arguments"]
                print(f"Signature for {entity_type} {entity_name}: {signature}")

                # Extract everything between the first set of parentheses
                arg_string = signature.split("(")[1].split(")")[0]

                # If the argument string is empty, return an empty string
                if not arg_string.strip():
                    return ""

                # Otherwise, split by spaces and take the first part
                arg_types = arg_string.split()[0]
                return arg_types.strip()

            return ""
        except:
            print(f"Failed to get the signature for {entity_type} {entity_name}.")
            return None

    def function_exists(self, function_name):
        return self._entity_exists(function_name, "USER FUNCTIONS")

    def sproc_exists(self, sproc_name):
        return self._entity_exists(sproc_name, "PROCEDURES")

    def get_function_signature(self, function_name):
        return self._get_entity_signature(function_name, "USER FUNCTIONS")

    def get_sproc_signature(self, sproc_name):
        return self._get_entity_signature(sproc_name, "PROCEDURES")

    def _drop_entity(self, entity_name, arg_type, entity_type):
        sql = f"DROP {entity_type} {entity_name}({arg_type})"
        print(sql)
        self.session.sql(sql).collect()

    def drop_function(self, function_name, arg_type):
        self._drop_entity(function_name, arg_type, "FUNCTION")

    def drop_sproc(self, sproc_name, arg_type):
        self._drop_entity(sproc_name, arg_type, "PROCEDURE")

    def register_sproc(
        self, func, function_name, packages, stage_location, imports, is_temp=False
    ):
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

    def register_udf(
        self, func, function_name, packages, stage_location, imports, is_temp=False
    ):
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

    def _register_entity(
        self,
        func,
        function_name,
        stage_location,
        packages,
        imports,
        is_sproc,
        is_temp=False,
    ):
        if is_sproc:
            self.register_sproc(
                func, function_name, packages, stage_location, imports, is_temp
            )
        else:
            self.register_udf(
                func, function_name, packages, stage_location, imports, is_temp
            )

    def _entity_signature(self, entity_name, is_sproc):
        if is_sproc:
            return self.get_sproc_signature(entity_name)
        return self.get_function_signature(entity_name)

    def _drop_temp_entity(self, temp_entity_name, temp_arg_type, is_sproc):
        if temp_arg_type is not None:
            if is_sproc and self.sproc_exists(temp_entity_name):
                self.drop_sproc(temp_entity_name, temp_arg_type)
            elif not is_sproc and self.function_exists(temp_entity_name):
                self.drop_function(temp_entity_name, temp_arg_type)

    def main(
        self, func, function_name, stage_location, packages, is_sproc, imports=None
    ):
        temp_entity_name = "temp_" + function_name

        try:
            print(colored("==========================================", "cyan"))

            print(
                colored(
                    f"Registering Temporary {('Sproc' if is_sproc else 'Function')}:",
                    "yellow",
                ),
                colored(temp_entity_name, "magenta"),
            )
            self._register_entity(
                func,
                temp_entity_name,
                stage_location,
                packages,
                imports,
                is_sproc,
                is_temp=True,
            )

            entity_type = "Sproc" if is_sproc else "Function"
            print(
                colored(
                    f"\n✅ {entity_type} {temp_entity_name} passed the test. Proceeding with deployment...",
                    "green",
                )
            )

            temp_arg_type = self._entity_signature(temp_entity_name, is_sproc)

            # Register main entity
            print(
                colored(f"\nDeploying Main {entity_type}:", "yellow"),
                colored(function_name, "magenta"),
            )
            self._register_entity(
                func, function_name, stage_location, packages, imports, is_sproc
            )

            self._drop_temp_entity(temp_entity_name, temp_arg_type, is_sproc)

            print(
                colored(
                    f"\n✅ {entity_type} {function_name} deployed successfully!", "green"
                )
            )

        except Exception as e:
            self._drop_temp_entity(temp_entity_name, temp_arg_type, is_sproc)
            print(colored(f"\n❌ Error deploying {entity_type}: {str(e)}", "red"))
            raise e

        print(colored("==========================================", "cyan"))
