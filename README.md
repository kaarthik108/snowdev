# SnowDev - Snowpark Devops

[![Documentation](https://img.shields.io/badge/documentation-view-blue)](docs/quickstart.md) [![Downloads](https://static.pepy.tech/badge/snowdev)](https://pepy.tech/project/snowdev)

SnowDev is a command-line utility designed for deploying various components related to Snowflake such as UDFs, stored procedures, and Streamlit applications using **Snowpark**. This tool streamlines tasks like initializing directories, local testing, uploading, and auto create components code using AI.

## Setup

```bash
 pyenv install 3.10.0 
 pyenv local 3.10.0 
 pip install snowdev or poetry add snowdev
 snowdev init
```

## Usage

``` bash
snowdev <command> [options]
```

## Commands

### `init`
- **Description**: Initializes the directory structure for the deployment.
- **Usage**: `snowdev init`

### `test`
- **Description**: Test the deployment locally.
- **Usage**: `snowdev test --udf predict_sentiment`

### `deploy`
- **Description**: Deploys the specified components, registers and tests using temp function before deploying to prod
- **Usage**: `snowdev deploy --udf predict_sentiment`

### `upload`
- **Description**: Uploads specified items such as static content.
- **Usage**: `snowdev upload --upload <upload_item>`

### `add`
- **Description**: Adds a package and optionally uploads it to stage.
- **Usage**: `snowdev add --package <package_name>`

### `new`
- **Description**: Adds a new component.
- **Usage**: `snowdev new --sproc "test_script"`

### `ai`
- **Description**: Interact with AI components and embeddings. It can also help in creating new AI components code based on the description, 
  make sure to have executed `snowdev ai --embed` to generate embeddings.
- **Usage**: `snowdev ai --streamlit "Want to see a bar chart on the order table"`

## Options

- `--udf <udf_name>`: Name or identifier for the UDF you want to deploy.
- `--sproc <sproc_name>`: Name or identifier for the Stored Procedure you want to deploy.
- `--streamlit <streamlit_name>`: Name or identifier for the Streamlit application you want to deploy. (This is still in PrPr)
- `--upload <upload_item>`: Specifies what to upload. Currently supported options: `static`.
- `--package <package_name>`: Specifies the name of the package to zip and upload to the static folder.
- `--embed`: Used with the `ai` command to run embeddings.

## Requirements

- **Python**: `>=3.10.0, <3.11.0`
- **Dependencies**: 
  - `"snowflake-snowpark-python" = { version = "1.5.1", extras = ["pandas"] }`


## Notes
- For the `ai` command, when specifying a component type (using --udf, --sproc, or --streamlit), ensure that the respective name or identifier is provided.
- When using the `add` command, the user will be prompted to decide if they want to upload the zip package to stage.
- The AI functionality in SnowDev is optimized with GPT-4, ensuring a better relevance in code suggestions and interactions.


## Roadmap

- [x] Support for UDFs and Stored Procedures
- [x] Support for Streamlit
- [x] AI interactions for embedding and suggestions
- [ ] Use AI to modify existing code for optimization
- [ ] AI to add the packages to toml file
- [ ] Adding more granularity for AI commands
- [ ] Support for snowflake Tasks



## Contributions

Feel free to contribute to SnowDev by submitting pull requests or opening issues on the project's GitHub repository.
