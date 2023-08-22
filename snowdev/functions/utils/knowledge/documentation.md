# Snowflake Session Methods
This document lists methods available in the Snowflake Session class, along with their documentation.

## _call

Private implementation of session.call

        Args:
            sproc_name: The name of stored procedure in Snowflake.
            args: Arguments should be basic Python types.
            statement_params: Dictionary of statement level parameters to be set while executing this action.
            is_return_table: When set to a non-null value, it signifies whether the return type of sproc_name
                is a table return type. This skips infer check and returns a dataframe with appropriate sql call.
        

## _get_client_side_session_parameter

It doesn't go to Snowflake to retrieve the session parameter.
        Use this only when you know the Snowflake session parameter is sent to the client when a session/connection is created.
        

## _resolve_imports

Resolve the imports and upload local files (if any) to the stage.

## _table_exists

 

## add_import


        Registers a remote file in stage or a local file as an import of a user-defined function
        (UDF). The local file can be a compressed file (e.g., zip), a Python file (.py),
        a directory, or any other file resource. You can also find examples in
        :class:`~snowflake.snowpark.udf.UDFRegistration`.

        Args:
            path: The path of a local file or a remote file in the stage. In each case:

                * if the path points to a local file, this file will be uploaded to the
                  stage where the UDF is registered and Snowflake will import the file when
                  executing that UDF.

                * if the path points to a local directory, the directory will be compressed
                  as a zip file and will be uploaded to the stage where the UDF is registered
                  and Snowflake will import the file when executing that UDF.

                * if the path points to a file in a stage, the file will be included in the
                  imports when executing a UDF.

            import_path: The relative Python import path for a UDF.
                If it is not provided or it is None, the UDF will import the package
                directly without any leading package/module. This argument will become
                a no-op if the path  points to a stage file or a non-Python local file.

        Example::

            >>> from snowflake.snowpark.types import IntegerType
            >>> from resources.test_udf_dir.test_udf_file import mod5
            >>> session.add_import("tests/resources/test_udf_dir/test_udf_file.py", import_path="resources.test_udf_dir.test_udf_file")
            >>> mod5_and_plus1_udf = session.udf.register(
            ...     lambda x: mod5(x) + 1,
            ...     return_type=IntegerType(),
            ...     input_types=[IntegerType()]
            ... )
            >>> session.range(1, 8, 2).select(mod5_and_plus1_udf("id")).to_df("col1").collect()
            [Row(COL1=2), Row(COL1=4), Row(COL1=1), Row(COL1=3)]
            >>> session.clear_imports()

        Note:
            1. In favor of the lazy execution, the file will not be uploaded to the stage
            immediately, and it will be uploaded when a UDF is created.

            2. The Snowpark library calculates a sha256 checksum for every file/directory.
            Each file is uploaded to a subdirectory named after the checksum for the
            file in the stage. If there is an existing file or directory, the Snowpark
            library will compare their checksums to determine whether it should be re-uploaded.
            Therefore, after uploading a local file to the stage, if the user makes
            some changes to this file and intends to upload it again, just call this
            function with the file path again, the existing file in the stage will be
            overwritten by the re-uploaded file.

            3. Adding two files with the same file name is not allowed, because UDFs
            can't be created with two imports with the same name.

            4. This method will register the file for all UDFs created later in the current
            session. If you only want to import a file for a specific UDF, you can use
            ``imports`` argument in :func:`functions.udf` or
            :meth:`session.udf.register() <snowflake.snowpark.udf.UDFRegistration.register>`.
        

## add_packages


        Adds third-party packages as dependencies of a user-defined function (UDF).
        Use this method to add packages for UDFs as installing packages using
        `conda <https://docs.conda.io/en/latest/>`_. You can also find examples in
        :class:`~snowflake.snowpark.udf.UDFRegistration`. See details of
        `third-party Python packages in Snowflake <https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html>`_.

        Args:
            packages: A `requirement specifier <https://packaging.python.org/en/latest/glossary/#term-Requirement-Specifier>`_,
                a ``module`` object or a list of them for installing the packages. An exception
                will be raised if two conflicting requirement specifiers are provided.
                The syntax of a requirement specifier is defined in full in
                `PEP 508 <https://www.python.org/dev/peps/pep-0508/>`_, but currently only the
                `version matching clause <https://www.python.org/dev/peps/pep-0440/#version-matching>`_ (``==``)
                is supported as a `version specifier <https://packaging.python.org/en/latest/glossary/#term-Version-Specifier>`_
                for this argument. If a ``module`` object is provided, the package will be
                installed with the version in the local environment.

        Example::

            >>> import numpy as np
            >>> from snowflake.snowpark.functions import udf
            >>> import numpy
            >>> import pandas
            >>> import dateutil
            >>> # add numpy with the latest version on Snowflake Anaconda
            >>> # and pandas with the version "1.3.*"
            >>> # and dateutil with the local version in your environment
            >>> session.add_packages("numpy", "pandas==1.4.*", dateutil)
            >>> @udf
            ... def get_package_name_udf() -> list:
            ...     return [numpy.__name__, pandas.__name__, dateutil.__name__]
            >>> session.sql(f"select {get_package_name_udf.name}()").to_df("col1").show()
            ----------------
            |"COL1"        |
            ----------------
            |[             |
            |  "numpy",    |
            |  "pandas",   |
            |  "dateutil"  |
            |]             |
            ----------------
            <BLANKLINE>
            >>> session.clear_packages()

        Note:
            1. This method will add packages for all UDFs created later in the current
            session. If you only want to add packages for a specific UDF, you can use
            ``packages`` argument in :func:`functions.udf` or
            :meth:`session.udf.register() <snowflake.snowpark.udf.UDFRegistration.register>`.

            2. We recommend you to `setup the local environment with Anaconda <https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#local-development-and-testing>`_,
            to ensure the consistent experience of a UDF between your local environment
            and the Snowflake server.
        

## add_requirements


        Adds a `requirement file <https://pip.pypa.io/en/stable/user_guide/#requirements-files>`_
        that contains a list of packages as dependencies of a user-defined function (UDF).

        Args:
            file_path: The path of a local requirement file.

        Example::

            >>> from snowflake.snowpark.functions import udf
            >>> import numpy
            >>> import pandas
            >>> # test_requirements.txt contains "numpy" and "pandas"
            >>> session.add_requirements("tests/resources/test_requirements.txt")
            >>> @udf
            ... def get_package_name_udf() -> list:
            ...     return [numpy.__name__, pandas.__name__]
            >>> session.sql(f"select {get_package_name_udf.name}()").to_df("col1").show()
            --------------
            |"COL1"      |
            --------------
            |[           |
            |  "numpy",  |
            |  "pandas"  |
            |]           |
            --------------
            <BLANKLINE>
            >>> session.clear_packages()

        Note:
            1. This method will add packages for all UDFs created later in the current
            session. If you only want to add packages for a specific UDF, you can use
            ``packages`` argument in :func:`functions.udf` or
            :meth:`session.udf.register() <snowflake.snowpark.udf.UDFRegistration.register>`.

            2. We recommend you to `setup the local environment with Anaconda <https://docs.snowflake.com/en/developer-guide/udf/python/udf-python-packages.html#local-development-and-testing>`_,
            to ensure the consistent experience of a UDF between your local environment
            and the Snowflake server.
        

## call

Calls a stored procedure by name.

        Args:
            sproc_name: The name of stored procedure in Snowflake.
            args: Arguments should be basic Python types.
            statement_params: Dictionary of statement level parameters to be set while executing this action.

        Example::

            >>> import snowflake.snowpark
            >>> from snowflake.snowpark.functions import sproc
            >>>
            >>> session.add_packages('snowflake-snowpark-python')
            >>>
            >>> @sproc(name="my_copy_sp", replace=True)
            ... def my_copy(session: snowflake.snowpark.Session, from_table: str, to_table: str, count: int) -> str:
            ...     session.table(from_table).limit(count).write.save_as_table(to_table)
            ...     return "SUCCESS"
            >>> _ = session.sql("create or replace table test_from(test_str varchar) as select randstr(20, random()) from table(generator(rowCount => 100))").collect()
            >>> _ = session.sql("drop table if exists test_to").collect()
            >>> session.call("my_copy_sp", "test_from", "test_to", 10)
            'SUCCESS'
            >>> session.table("test_to").count()
            10

        Example::

            >>> from snowflake.snowpark.dataframe import DataFrame
            >>>
            >>> @sproc(name="my_table_sp", replace=True)
            ... def my_table(session: snowflake.snowpark.Session, x: int, y: int, col1: str, col2: str) -> DataFrame:
            ...     return session.sql(f"select {x} as {col1}, {y} as {col2}")
            >>> session.call("my_table_sp", 1, 2, "a", "b").show()
            -------------
            |"A"  |"B"  |
            -------------
            |1    |2    |
            -------------
            <BLANKLINE>
        

## cancel_all


        Cancel all action methods that are running currently.
        This does not affect any action methods called in the future.
        

## clear_imports


        Clears all files in a stage or local files from the imports of a user-defined function (UDF).
        

## clear_packages


        Clears all third-party packages of a user-defined function (UDF).
        

## close

Close this session.

## createDataFrame

Creates a new DataFrame containing the specified values from the local data.

        If creating a new DataFrame from a pandas Dataframe, we will store the pandas
        DataFrame in a temporary table and return a DataFrame pointing to that temporary
        table for you to then do further transformations on. This temporary table will be
        dropped at the end of your session. If you would like to save the pandas DataFrame,
        use the :meth:`write_pandas` method instead.

        Args:
            data: The local data for building a :class:`DataFrame`. ``data`` can only
                be a :class:`list`, :class:`tuple` or pandas DataFrame. Every element in
                ``data`` will constitute a row in the DataFrame.
            schema: A :class:`~snowflake.snowpark.types.StructType` containing names and
                data types of columns, or a list of column names, or ``None``.
                When ``schema`` is a list of column names or ``None``, the schema of the
                DataFrame will be inferred from the data across all rows. To improve
                performance, provide a schema. This avoids the need to infer data types
                with large data sets.

        Examples::

            >>> # create a dataframe with a schema
            >>> from snowflake.snowpark.types import IntegerType, StringType, StructField
            >>> schema = StructType([StructField("a", IntegerType()), StructField("b", StringType())])
            >>> session.create_dataframe([[1, "snow"], [3, "flake"]], schema).collect()
            [Row(A=1, B='snow'), Row(A=3, B='flake')]

            >>> # create a dataframe by inferring a schema from the data
            >>> from snowflake.snowpark import Row
            >>> # infer schema
            >>> session.create_dataframe([1, 2, 3, 4], schema=["a"]).collect()
            [Row(A=1), Row(A=2), Row(A=3), Row(A=4)]
            >>> session.create_dataframe([[1, 2, 3, 4]], schema=["a", "b", "c", "d"]).collect()
            [Row(A=1, B=2, C=3, D=4)]
            >>> session.create_dataframe([[1, 2], [3, 4]], schema=["a", "b"]).collect()
            [Row(A=1, B=2), Row(A=3, B=4)]
            >>> session.create_dataframe([Row(a=1, b=2, c=3, d=4)]).collect()
            [Row(A=1, B=2, C=3, D=4)]
            >>> session.create_dataframe([{"a": 1}, {"b": 2}]).collect()
            [Row(A=1, B=None), Row(A=None, B=2)]

            >>> # create a dataframe from a pandas Dataframe
            >>> import pandas as pd
            >>> session.create_dataframe(pd.DataFrame([(1, 2, 3, 4)], columns=["a", "b", "c", "d"])).collect()
            [Row(a=1, b=2, c=3, d=4)]
        

## create_async_job


        Creates an :class:`AsyncJob` from a query ID.

        See also:
            :class:`AsyncJob`
        

## create_dataframe

Creates a new DataFrame containing the specified values from the local data.

        If creating a new DataFrame from a pandas Dataframe, we will store the pandas
        DataFrame in a temporary table and return a DataFrame pointing to that temporary
        table for you to then do further transformations on. This temporary table will be
        dropped at the end of your session. If you would like to save the pandas DataFrame,
        use the :meth:`write_pandas` method instead.

        Args:
            data: The local data for building a :class:`DataFrame`. ``data`` can only
                be a :class:`list`, :class:`tuple` or pandas DataFrame. Every element in
                ``data`` will constitute a row in the DataFrame.
            schema: A :class:`~snowflake.snowpark.types.StructType` containing names and
                data types of columns, or a list of column names, or ``None``.
                When ``schema`` is a list of column names or ``None``, the schema of the
                DataFrame will be inferred from the data across all rows. To improve
                performance, provide a schema. This avoids the need to infer data types
                with large data sets.

        Examples::

            >>> # create a dataframe with a schema
            >>> from snowflake.snowpark.types import IntegerType, StringType, StructField
            >>> schema = StructType([StructField("a", IntegerType()), StructField("b", StringType())])
            >>> session.create_dataframe([[1, "snow"], [3, "flake"]], schema).collect()
            [Row(A=1, B='snow'), Row(A=3, B='flake')]

            >>> # create a dataframe by inferring a schema from the data
            >>> from snowflake.snowpark import Row
            >>> # infer schema
            >>> session.create_dataframe([1, 2, 3, 4], schema=["a"]).collect()
            [Row(A=1), Row(A=2), Row(A=3), Row(A=4)]
            >>> session.create_dataframe([[1, 2, 3, 4]], schema=["a", "b", "c", "d"]).collect()
            [Row(A=1, B=2, C=3, D=4)]
            >>> session.create_dataframe([[1, 2], [3, 4]], schema=["a", "b"]).collect()
            [Row(A=1, B=2), Row(A=3, B=4)]
            >>> session.create_dataframe([Row(a=1, b=2, c=3, d=4)]).collect()
            [Row(A=1, B=2, C=3, D=4)]
            >>> session.create_dataframe([{"a": 1}, {"b": 2}]).collect()
            [Row(A=1, B=None), Row(A=None, B=2)]

            >>> # create a dataframe from a pandas Dataframe
            >>> import pandas as pd
            >>> session.create_dataframe(pd.DataFrame([(1, 2, 3, 4)], columns=["a", "b", "c", "d"])).collect()
            [Row(a=1, b=2, c=3, d=4)]
        

## flatten

Creates a new :class:`DataFrame` by flattening compound values into multiple rows.

        The new :class:`DataFrame` will consist of the following columns:

            - SEQ
            - KEY
            - PATH
            - INDEX
            - VALUE
            - THIS

        References: `Snowflake SQL function FLATTEN <https://docs.snowflake.com/en/sql-reference/functions/flatten.html>`_.

        Example::

            df = session.flatten(parse_json(lit('{"a":[1,2]}')), "a", False, False, "BOTH")

        Args:
            input: The name of a column or a :class:`Column` instance that will be unseated into rows.
                The column data must be of Snowflake data type VARIANT, OBJECT, or ARRAY.
            path: The path to the element within a VARIANT data structure which needs to be flattened.
                The outermost element is to be flattened if path is empty or ``None``.
            outer: If ``False``, any input rows that cannot be expanded, either because they cannot be accessed in the ``path``
                or because they have zero fields or entries, are completely omitted from the output.
                Otherwise, exactly one row is generated for zero-row expansions
                (with NULL in the KEY, INDEX, and VALUE columns).
            recursive: If ``False``, only the element referenced by ``path`` is expanded.
                Otherwise, the expansion is performed for all sub-elements recursively.
            mode: Specifies which types should be flattened "OBJECT", "ARRAY", or "BOTH".

        Returns:
            A new :class:`DataFrame` that has the flattened new columns and new rows from the compound data.

        Example::

            >>> from snowflake.snowpark.functions import lit, parse_json
            >>> session.flatten(parse_json(lit('{"a":[1,2]}')), path="a", outer=False, recursive=False, mode="BOTH").show()
            -------------------------------------------------------
            |"SEQ"  |"KEY"  |"PATH"  |"INDEX"  |"VALUE"  |"THIS"  |
            -------------------------------------------------------
            |1      |NULL   |a[0]    |0        |1        |[       |
            |       |       |        |         |         |  1,    |
            |       |       |        |         |         |  2     |
            |       |       |        |         |         |]       |
            |1      |NULL   |a[1]    |1        |2        |[       |
            |       |       |        |         |         |  1,    |
            |       |       |        |         |         |  2     |
            |       |       |        |         |         |]       |
            -------------------------------------------------------
            <BLANKLINE>

        See Also:
            - :meth:`DataFrame.flatten`, which creates a new :class:`DataFrame` by exploding a VARIANT column of an existing :class:`DataFrame`.
            - :meth:`Session.table_function`, which can be used for any Snowflake table functions, including ``flatten``.
        

        This function or method is deprecated since 0.7.0. Use :meth:`table_function` instead. 




## generator

Creates a new DataFrame using the Generator table function.

        References: `Snowflake Generator function <https://docs.snowflake.com/en/sql-reference/functions/generator.html>`_.

        Args:
            columns: List of data generation function that work in tandem with generator table function.
            rowcount: Resulting table with contain ``rowcount`` rows if only this argument is specified. Defaults to 0.
            timelimit: The query runs for ``timelimit`` seconds, generating as many rows as possible within the time frame. The
                exact row count depends on the system speed. Defaults to 0.

        Usage Notes:
                - When both ``rowcount`` and ``timelimit`` are specified, then:

                    + if the ``rowcount`` is reached before the ``timelimit``, the resulting table with contain ``rowcount`` rows.
                    + if the ``timelimit`` is reached before the ``rowcount``, the table will contain as many rows generated within this time.
                - If both ``rowcount`` and ``timelimit`` are not specified, 0 rows will be generated.

        Example 1
            >>> from snowflake.snowpark.functions import seq1, seq8, uniform
            >>> df = session.generator(seq1(1).as_("sequence one"), uniform(1, 10, 2).as_("uniform"), rowcount=3)
            >>> df.show()
            ------------------------------
            |"sequence one"  |"UNIFORM"  |
            ------------------------------
            |0               |3          |
            |1               |3          |
            |2               |3          |
            ------------------------------
            <BLANKLINE>

        Example 2
            >>> df = session.generator(seq8(0), uniform(1, 10, 2), timelimit=1).order_by(seq8(0)).limit(3)
            >>> df.show()
            -----------------------------------
            |"SEQ8(0)"  |"UNIFORM(1, 10, 2)"  |
            -----------------------------------
            |0          |3                    |
            |1          |3                    |
            |2          |3                    |
            -----------------------------------
            <BLANKLINE>

        Returns:
            A new :class:`DataFrame` with data from calling the generator table function.
        

## get_current_account


        Returns the name of the current account for the Python connector session attached
        to this session.
        

## get_current_database


        Returns the name of the current database for the Python connector session attached
        to this session. See the example in :meth:`table`.
        

## get_current_role


        Returns the name of the primary role in use for the current session.
        

## get_current_schema


        Returns the name of the current schema for the Python connector session attached
        to this session. See the example in :meth:`table`.
        

## get_current_warehouse


        Returns the name of the warehouse in use for the current session.
        

## get_fully_qualified_current_schema

Returns the fully qualified name of the current schema for the session.

## get_imports


        Returns a list of imports added for user defined functions (UDFs).
        This list includes any Python or zip files that were added automatically by the library.
        

## get_packages


        Returns a ``dict`` of packages added for user-defined functions (UDFs).
        The key of this ``dict`` is the package name and the value of this ``dict``
        is the corresponding requirement specifier.
        

## get_session_stage


        Returns the name of the temporary stage created by the Snowpark library
        for uploading and storing temporary artifacts for this session.
        These artifacts include libraries and packages for UDFs that you define
        in this session via :func:`add_import`.
        

## query_history

Create an instance of :class:`QueryHistory` as a context manager to record queries that are pushed down to the Snowflake database.

        >>> with session.query_history() as query_history:
        ...     df = session.create_dataframe([[1, 2], [3, 4]], schema=["a", "b"])
        ...     df = df.filter(df.a == 1)
        ...     res = df.collect()
        >>> assert len(query_history.queries) == 1
        

## range


        Creates a new DataFrame from a range of numbers. The resulting DataFrame has
        single column named ``ID``, containing elements in a range from ``start`` to
        ``end`` (exclusive) with the step value ``step``.

        Args:
            start: The start of the range. If ``end`` is not specified,
                ``start`` will be used as the value of ``end``.
            end: The end of the range.
            step: The step of the range.

        Examples::

            >>> session.range(10).collect()
            [Row(ID=0), Row(ID=1), Row(ID=2), Row(ID=3), Row(ID=4), Row(ID=5), Row(ID=6), Row(ID=7), Row(ID=8), Row(ID=9)]
            >>> session.range(1, 10).collect()
            [Row(ID=1), Row(ID=2), Row(ID=3), Row(ID=4), Row(ID=5), Row(ID=6), Row(ID=7), Row(ID=8), Row(ID=9)]
            >>> session.range(1, 10, 2).collect()
            [Row(ID=1), Row(ID=3), Row(ID=5), Row(ID=7), Row(ID=9)]
        

## remove_import


        Removes a file in stage or local file from the imports of a user-defined function (UDF).

        Args:
            path: a path pointing to a local file or a remote file in the stage

        Examples::

            >>> session.clear_imports()
            >>> len(session.get_imports())
            0
            >>> session.add_import("tests/resources/test_udf_dir/test_udf_file.py")
            >>> len(session.get_imports())
            1
            >>> session.remove_import("tests/resources/test_udf_dir/test_udf_file.py")
            >>> len(session.get_imports())
            0
        

## remove_package


        Removes a third-party package from the dependency list of a user-defined function (UDF).

        Args:
            package: The package name.

        Examples::

            >>> session.clear_packages()
            >>> len(session.get_packages())
            0
            >>> session.add_packages("numpy", "pandas==1.3.5")
            >>> len(session.get_packages())
            2
            >>> session.remove_package("numpy")
            >>> len(session.get_packages())
            1
            >>> session.remove_package("pandas")
            >>> len(session.get_packages())
            0
        

## sql


        Returns a new DataFrame representing the results of a SQL query.
        You can use this method to execute a SQL statement. Note that you still
        need to call :func:`DataFrame.collect` to execute this query in Snowflake.

        Args:
            query: The SQL statement to execute.
            params: binding parameters.

        Example::

            >>> # create a dataframe from a SQL query
            >>> df = session.sql("select 1/2")
            >>> # execute the query
            >>> df.collect()
            [Row(1/2=Decimal('0.500000'))]
        

## table


        Returns a Table that points the specified table.

        Args:
            name: A string or list of strings that specify the table name or
                fully-qualified object identifier (database name, schema name, and table name).

            Note:
                If your table name contains special characters, use double quotes to mark it like this, ``session.table('"my table"')``.
                For fully qualified names, you need to use double quotes separately like this, ``session.table('"my db"."my schema"."my.table"')``.
                Refer to `Identifier Requirements <https://docs.snowflake.com/en/sql-reference/identifiers-syntax.html>`_.

        Examples::

            >>> df1 = session.create_dataframe([[1, 2], [3, 4]], schema=["a", "b"])
            >>> df1.write.save_as_table("my_table", mode="overwrite", table_type="temporary")
            >>> session.table("my_table").collect()
            [Row(A=1, B=2), Row(A=3, B=4)]
            >>> current_db = session.get_current_database()
            >>> current_schema = session.get_current_schema()
            >>> session.table([current_db, current_schema, "my_table"]).collect()
            [Row(A=1, B=2), Row(A=3, B=4)]
        

## table_function

Creates a new DataFrame from the given snowflake SQL table function.

        References: `Snowflake SQL functions <https://docs.snowflake.com/en/sql-reference/functions-table.html>`_.

        Example 1
            Query a table function by function name:

            >>> from snowflake.snowpark.functions import lit
            >>> session.table_function("split_to_table", lit("split words to table"), lit(" ")).collect()
            [Row(SEQ=1, INDEX=1, VALUE='split'), Row(SEQ=1, INDEX=2, VALUE='words'), Row(SEQ=1, INDEX=3, VALUE='to'), Row(SEQ=1, INDEX=4, VALUE='table')]

        Example 2
            Define a table function variable and query it:

            >>> from snowflake.snowpark.functions import table_function, lit
            >>> split_to_table = table_function("split_to_table")
            >>> session.table_function(split_to_table(lit("split words to table"), lit(" "))).collect()
            [Row(SEQ=1, INDEX=1, VALUE='split'), Row(SEQ=1, INDEX=2, VALUE='words'), Row(SEQ=1, INDEX=3, VALUE='to'), Row(SEQ=1, INDEX=4, VALUE='table')]

        Example 3
            If you want to call a UDTF right after it's registered, the returned ``UserDefinedTableFunction`` is callable:

            >>> from snowflake.snowpark.types import IntegerType, StructField, StructType
            >>> from snowflake.snowpark.functions import udtf, lit
            >>> class GeneratorUDTF:
            ...     def process(self, n):
            ...         for i in range(n):
            ...             yield (i, )
            >>> generator_udtf = udtf(GeneratorUDTF, output_schema=StructType([StructField("number", IntegerType())]), input_types=[IntegerType()])
            >>> session.table_function(generator_udtf(lit(3))).collect()
            [Row(NUMBER=0), Row(NUMBER=1), Row(NUMBER=2)]

        Args:
            func_name: The SQL function name.
            func_arguments: The positional arguments for the SQL function.
            func_named_arguments: The named arguments for the SQL function, if it accepts named arguments.

        Returns:
            A new :class:`DataFrame` with data from calling the table function.

        See Also:
            - :meth:`DataFrame.join_table_function`, which lateral joins an existing :class:`DataFrame` and a SQL function.
            - :meth:`Session.generator`, which is used to instantiate a :class:`DataFrame` using Generator table function.
                Generator functions are not supported with :meth:`Session.table_function`.
        

## use_database

Specifies the active/current database for the session.

        Args:
            database: The database name.
        

## use_role

Specifies the active/current primary role for the session.

        Args:
            role: the role name.
        

## use_schema

Specifies the active/current schema for the session.

        Args:
            schema: The schema name.
        

## use_secondary_roles


        Specifies the active/current secondary roles for the session.
        The currently-active secondary roles set the context that determines whether
        the current user has the necessary privileges to perform SQL actions.

        Args:
            roles: "all" or "none". ``None`` means "none".

        References: `Snowflake command USE SECONDARY ROLES <https://docs.snowflake.com/en/sql-reference/sql/use-secondary-roles.html>`_.
        

## use_warehouse

Specifies the active/current warehouse for the session.

        Args:
            warehouse: the warehouse name.
        

## write_pandas

Writes a pandas DataFrame to a table in Snowflake and returns a
        Snowpark :class:`DataFrame` object referring to the table where the
        pandas DataFrame was written to.

        Args:
            df: The pandas DataFrame we'd like to write back.
            table_name: Name of the table we want to insert into.
            database: Database that the table is in. If not provided, the default one will be used.
            schema: Schema that the table is in. If not provided, the default one will be used.
            chunk_size: Number of rows to be inserted once. If not provided, all rows will be dumped once.
                Default to None normally, 100,000 if inside a stored procedure.
            compression: The compression used on the Parquet files: gzip or snappy. Gzip gives supposedly a
                better compression, while snappy is faster. Use whichever is more appropriate.
            on_error: Action to take when COPY INTO statements fail. See details at
                `copy options <https://docs.snowflake.com/en/sql-reference/sql/copy-into-table.html#copy-options-copyoptions>`_.
            parallel: Number of threads to be used when uploading chunks. See details at
                `parallel parameter <https://docs.snowflake.com/en/sql-reference/sql/put.html#optional-parameters>`_.
            quote_identifiers: By default, identifiers, specifically database, schema, table and column names
                (from :attr:`DataFrame.columns`) will be quoted. If set to ``False``, identifiers
                are passed on to Snowflake without quoting, i.e. identifiers will be coerced to uppercase by Snowflake.
            auto_create_table: When true, automatically creates a table to store the passed in pandas DataFrame using the
                passed in ``database``, ``schema``, and ``table_name``. Note: there are usually multiple table configurations that
                would allow you to upload a particular pandas DataFrame successfully. If you don't like the auto created
                table, you can always create your own table before calling this function. For example, auto-created
                tables will store :class:`list`, :class:`tuple` and :class:`dict` as strings in a VARCHAR column.
            create_temp_table: (Deprecated) The to-be-created table will be temporary if this is set to ``True``. Note
                that to avoid breaking changes, currently when this is set to True, it overrides ``table_type``.
            overwrite: Default value is ``False`` and the Pandas DataFrame data is appended to the existing table. If set to ``True`` and if auto_create_table is also set to ``True``,
                then it drops the table. If set to ``True`` and if auto_create_table is set to ``False``,
                then it truncates the table. Note that in both cases (when overwrite is set to ``True``) it will replace the existing
                contents of the table with that of the passed in Pandas DataFrame.
            table_type: The table type of table to be created. The supported values are: ``temp``, ``temporary``,
                        and ``transient``. An empty string means to create a permanent table. Learn more about table
                        types `here <https://docs.snowflake.com/en/user-guide/tables-temp-transient.html>`_.

        Example::

            >>> import pandas as pd
            >>> pandas_df = pd.DataFrame([(1, "Steve"), (2, "Bob")], columns=["id", "name"])
            >>> snowpark_df = session.write_pandas(pandas_df, "write_pandas_table", auto_create_table=True, table_type="temp")
            >>> snowpark_df.to_pandas()
               id   name
            0   1  Steve
            1   2    Bob

            >>> pandas_df2 = pd.DataFrame([(3, "John")], columns=["id", "name"])
            >>> snowpark_df2 = session.write_pandas(pandas_df2, "write_pandas_table", auto_create_table=False)
            >>> snowpark_df2.to_pandas()
               id   name
            0   1  Steve
            1   2    Bob
            2   3   John

            >>> pandas_df3 = pd.DataFrame([(1, "Jane")], columns=["id", "name"])
            >>> snowpark_df3 = session.write_pandas(pandas_df3, "write_pandas_table", auto_create_table=False, overwrite=True)
            >>> snowpark_df3.to_pandas()
               id  name
            0   1  Jane

            >>> pandas_df4 = pd.DataFrame([(1, "Jane")], columns=["id", "name"])
            >>> snowpark_df4 = session.write_pandas(pandas_df4, "write_pandas_transient_table", auto_create_table=True, table_type="transient")
            >>> snowpark_df4.to_pandas()
               id  name
            0   1  Jane

        Note:
            Unless ``auto_create_table`` is ``True``, you must first create a table in
            Snowflake that the passed in pandas DataFrame can be written to. If
            your pandas DataFrame cannot be written to the specified table, an
            exception will be raised.
        

