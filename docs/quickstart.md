# Quickstart Guide for SnowDev

Welcome to SnowDev's quickstart guide! In just a few minutes, you'll be up and running with SnowDev, ready to deploy components related to Snowflake using Snowpark.

## Installation

**Setup Python Environment**

Ensure you have Python version `3.10` and above.

```bash
pyenv install 3.10.0 
pyenv local 3.10.0 
```

### Install SnowDev
You can install SnowDev using pip or add it with poetry.

```bash
pip install snowdev
```

### Initialize SnowDev
Start your SnowDev journey by initializing the directory structure for deployment, this will create necessary folders src and udf, sproc, streamlit components

```bash
snowdev init
```

## First Deployment with SnowDev

Now that you have SnowDev installed and initialized, it's time to see it in action! Let's walk through the deployment of various components.

### Deploying Stored Procedures

1. **Add a New Stored Procedure**
  
    Add a new stored procedure named `test_script`:

    ```bash
    snowdev new --sproc test_script
    ```

2. **Test the Stored Procedure Locally**

    Now, test your stored procedure locally to ensure everything works as expected:

    ```bash
    snowdev test --sproc test_script
    ```

3. **Deploy the Stored Procedure to Production**

    Satisfied with the local tests? Let's deploy it to production:

    ```bash
    snowdev deploy --sproc test_script
    ```

---

### Deploying User-Defined Functions (UDFs)

1. **Add a New UDF**

    Create a new UDF named `predict_sentiment`:

    ```bash
    snowdev new --udf predict_sentiment
    ```

2. **Test the UDF Locally**

    Before deploying, test the UDF locally to ensure it behaves as intended:

    ```bash
    snowdev test --udf predict_sentiment
    ```

3. **Deploy the UDF to Production**

    Once local testing is complete, deploy the UDF to production:

    ```bash
    snowdev deploy --udf predict_sentiment
    ```

---

### Deploying Streamlit Applications

1. **Add a New Streamlit Application**

    Create a new Streamlit application named `order_chart_app`:

    ```bash
    snowdev new --streamlit "order_chart_app"
    ```

2. **Deploy the Streamlit Application to Production**

    Ready to go live? Deploy the application to production:

    ```bash
    snowdev deploy --streamlit "order_chart_app"
    ```

---
### Deploying Tasks

1. **Add a New snowflake Task**

    Create a new task application named `sample_task`:

    ```bash
    snowdev new --task "sample_task"
    ```

    Modify the sql in the src/task/sample_task/app.sql

2. **Deploy the task Application to Production**

    Ready to go live? Deploy the application to production:

    ```bash
    snowdev deploy --task "sample_task"
    ```

3. **Resume the Task**

    Resume the task so it starts the schedule:

    ```bash
    snowdev task --name "sample_task" --action resume
    ```

---

### Deploying using AI

1. **Initialize by embedding the knowledge**

    This embeds the knowledge base into a in memory chroma db vector DB:

    ```bash
    snowdev ai --embed
    ```

2. **Deploy a new stored procedure using AI**

    Give a clear description of what you need the stored procedure to do:

    ```bash
    snowdev ai --sproc "I want to fetch data from order table and predict the bad orders using snowflake ml"
    ```

---

**Congratulations!** You've successfully deployed various components using SnowDev. Dive deeper and explore other commands and options mentioned in the main README to make the most out of SnowDev.
