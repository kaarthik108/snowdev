# Example how to create stored procedure in snowflake.

"""
This script provides a generalized framework to fetch data from Snowflake, preprocess it, 
train a machine learning model using Snowflake's Snowpark, and then evaluate the model 
using various metrics. It's designed to be adaptable for multiple scenarios simply by 
modifying the feature columns, target columns, and the specific machine learning model 
you wish to use.
"""

import os

from joblib import dump
from snowflake.ml.modeling.metrics import (
    mean_absolute_percentage_error,
    mean_squared_error,
    r2_score,
)
from snowflake.ml.modeling.pipeline import Pipeline
from snowflake.ml.modeling.preprocessing import MinMaxScaler
from snowflake.ml.modeling.xgboost import XGBClassifier
from snowflake.snowpark import Session
from snowflake.snowpark.types import FloatType


def handler(
    session: Session,
    data_table: str,
    feature_cols: list,
    target_col: str,
    storage_path: str,
) -> dict:
    """
    Generalized function to fetch data, train a machine learning model and evaluate its performance.

    Args:
        session (Session): Snowflake session to run SQL commands.
        data_table (str): Name of the table from where data is to be fetched.
        feature_cols (list): List of feature column names.
        target_col (str): The target column name for supervised learning.
        storage_path (str): Directory path to save the trained model.

    Returns:
        dict: Dictionary containing model performance metrics.
    """

    # Fetch data from Snowflake
    df = session.sql(f"select * from {data_table}")

    # Cast feature columns to FloatType
    for col in feature_cols:
        new_col = df.col(col).cast(FloatType())
        df = df.with_column(col, new_col)

    # Define machine learning pipeline
    pipeline = Pipeline(
        steps=[
            ("scaler", MinMaxScaler(input_cols=feature_cols, output_cols=feature_cols)),
            (
                "classifier",
                XGBClassifier(
                    input_cols=feature_cols,
                    output_cols=["prediction"],
                    label_cols=target_col,
                    n_jobs=-1,
                ),
            ),
        ]
    )

    # Split data into training and test sets
    train_df, test_df = df.random_split(weights=[0.8, 0.2], seed=0)

    # Train the model
    model = pipeline.fit(train_df)

    # Predict on the test set
    predictions = model.predict(test_df)

    # Evaluate model's performance
    mape = mean_absolute_percentage_error(
        df=predictions, y_true_col_names=target_col, y_pred_col_names="prediction"
    )
    mse = mean_squared_error(
        df=predictions, y_true_col_names=target_col, y_pred_col_names="prediction"
    )
    r2 = r2_score(
        df=predictions, y_true_col_name=target_col, y_pred_col_name="prediction"
    )

    # Convert the model into sklearn format and save
    sklearn_model = model.to_sklearn()
    model_output_dir = "/tmp"
    model_file_path = os.path.join(model_output_dir, "trained_model.joblib")
    dump(sklearn_model, model_file_path)
    session.file.put(model_file_path, f"@{storage_path}", overwrite=True)

    return {"mape": mape, "mse": mse, "r2": r2}


if __name__ == "__main__":

    from snowdev import SnowflakeConnection

    session = SnowflakeConnection().get_session()
    data_table = "SNOWDEV.ML_DATA"
    feature_cols = ["feature_1", "feature_2", "feature_3"]
    target_col = "target"
    storage_path = "snowdev/models/trained_model.joblib"
    handler(session, data_table, feature_cols, target_col, storage_path)
