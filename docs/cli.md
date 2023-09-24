# SnowDev CLI Documentation

SnowDev is a CLI tool designed to deploy Snowflake components such as UDFs, Stored Procedures, Streamlit apps, and tasks. Below is the detailed documentation of all the commands available in the SnowDev CLI.

## 1. `init`
- **Description**: Initialize the project structure.
- **Usage**: `snowdev init`

## 2. `new`
- **Description**: Create a new component.
- **Usage**: `snowdev new [OPTIONS]`
- **Options**:
    - `--udf <udf_name>`: The name of the UDF.
    - `--sproc <sproc_name>`: The name of the stored procedure.
    - `--streamlit <streamlit_name>`: The name of the Streamlit app.
    - `--task <task_name>`: The name of the task.

## 3. `test`
- **Description**: Test the deployment.
- **Usage**: `snowdev test [OPTIONS]`
- **Options**:
    - `--udf <udf_name>`: The name of the UDF.
    - `--sproc <sproc_name>`: The name of the stored procedure.

## 4. `upload`
- **Description**: Upload static content to stage, only for zipped external packages.
- **Usage**: `snowdev upload`

## 5. `add`
- **Description**: Add a package and optionally upload.
- **Usage**: `snowdev add --package <package_name>`

## 6. `ai`
- **Description**: Interact with AI components. Run embeddings or create new AI components.
- **Usage**: `snowdev ai [OPTIONS]`
- **Options**:
    - `--udf <udf_name>`: The name of the UDF.
    - `--sproc <sproc_name>`: The name of the stored procedure.
    - `--streamlit <streamlit_name>`: The name of the Streamlit app.
    - `--embed`: Run the embeddings.
    - `--task <task_name>`: The name of the task.

## 7. `deploy`
- **Description**: Deploy components.
- **Usage**: `snowdev deploy [OPTIONS]`
- **Options**:
    - `--udf <udf_name>`: The name of the UDF.
    - `--sproc <sproc_name>`: The name of the stored procedure.
    - `--streamlit <streamlit_name>`: The name of the Streamlit app.
    - `--task <task_name>`: The name of the task.

## 8. `task`
- **Description**: Commands for tasks. Actions: resume, suspend, execute.
- **Usage**: `snowdev task --name <task_name> --action <action>`
- **Options**:
    - `--name <task_name>`: The name of the task. (Required)
    - `--action <action>`: The action to be performed on the task. Choices: resume, suspend, execute. (Required)
