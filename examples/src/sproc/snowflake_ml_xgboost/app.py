from snowflake.snowpark import Session
import os
from joblib import dump
from snowflake.ml.modeling.pipeline import Pipeline
from snowflake.ml.modeling.xgboost import XGBClassifier
from snowflake.ml.modeling.preprocessing import OneHotEncoder, StandardScaler
from snowflake.ml.modeling.metrics import mean_absolute_percentage_error
from snowflake.ml.modeling.metrics import (
    mean_squared_error,
    mean_absolute_percentage_error,
    r2_score,
)


def handler(
    session: Session,
    database_name: str,
    schema_name: str,
    table_name: str,
    numerical_cols: list,
    categorical_cols: list,
    target_col: str,
    stage_location: str,
    seed: int = 42,
):
    """
    Generalized function to train a model with given parameters and save it.
    """

    # 1. Data Collection
    query = f"SELECT * FROM {database_name}.{schema_name}.{table_name}"
    df = session.sql(query)

    # 2. Data Cleaning and Preprocessing
    # Handling Numerical Columns
    for col in numerical_cols:
        df = df.with_column(col, df.col(col).cast("FLOAT"))

    # Handle Categorical Columns
    encoder = OneHotEncoder(
        input_cols=categorical_cols,
        output_cols=[f"{col}_encoded" for col in categorical_cols],
    )
    df = encoder.fit_transform(df)

    feature_cols = numerical_cols + [f"{col}_encoded" for col in categorical_cols]

    # 3. Data Splitting
    train_df, test_df = df.random_split(weights=[0.8, 0.2], seed=seed)

    # 4. Model Definition
    pipeline = Pipeline(
        steps=[
            (
                "Scaler",
                StandardScaler(input_cols=numerical_cols, output_cols=numerical_cols),
            ),
            (
                "Classifier",
                XGBClassifier(
                    input_cols=feature_cols,
                    output_cols=["prediction"],
                    label_cols=target_col,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    # 5. Model Training
    model = pipeline.fit(train_df)

    # 6. Model Evaluation
    result = model.predict(test_df)
    mape = mean_absolute_percentage_error(
        df=result, y_true_col_names=target_col, y_pred_col_names="prediction"
    )
    mse = mean_squared_error(
        df=result, y_true_col_names=target_col, y_pred_col_names="prediction"
    )
    r2 = r2_score(df=result, y_true_col_name=target_col, y_pred_col_name="prediction")

    # 7. Model Saving
    model_output_dir = "/tmp"
    model_file = os.path.join(model_output_dir, f"model_{table_name}.joblib")
    dump(model.to_sklearn(), model_file)
    session.file.put(model_file, f"@{stage_location}", overwrite=True)

    # 8. Results
    return {"mape": mape, "mse": mse, "r2": r2}


# Local testing
if __name__ == "__main__":
    from snowdev import SnowflakeConnection

    session = SnowflakeConnection().get_session()
    # Define parameters
    database_name = "your_database"
    schema_name = "your_schema"
    table_name = "your_table"
    numerical_cols = ["numerical_feature1", "numerical_feature2"]
    categorical_cols = ["categorical_feature1", "categorical_feature2"]
    target_col = "target"
    stage_location = "your_stage_location"

    # Call the handler function
    metrics = handler(
        session,
        database_name,
        schema_name,
        table_name,
        numerical_cols,
        categorical_cols,
        target_col,
        stage_location,
    )
    print(metrics)
