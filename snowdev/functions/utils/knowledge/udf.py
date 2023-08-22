# This is an example of how to create snowflake snowpark function UDF(user defined function) in snowflake.

import os
import sys
import cachetools
import pandas

from snowflake.snowpark.types import PandasSeries
from nltk.sentiment.vader import SentimentIntensityAnalyzer


@cachetools.cached(cache={})
def load_model(filename):
    """
     This function is used to load the sentiment model

    Parameters
    ----------
    filename : str
        The name of the file to load

    Returns
    -------
    SentimentIntensityAnalyzer
        A sentiment model
    """
    IMPORT_DIRECTORY_NAME = "snowflake_import_directory"
    import_dir = sys._xoptions[IMPORT_DIRECTORY_NAME]

    if import_dir:
        # m = SentimentIntensityAnalyzer(lexicon_file=os.path.join(import_dir, filename))
        return None


def handler(df: str) -> str:
    """
    This function is used to get sentiment score for a given text

    Parameters
    ----------
    df : PandasSeries[str]
        A pandas series of text

    Returns
    -------
    PandasSeries[float]
        A pandas series of sentiment score
    """
    sia = load_model(filename="vader_lexicon.txt")
    return df[0].apply(lambda x: sia.polarity_scores(str(x))["compound"])
    return df


# for vectorized input
handler._sf_vectorized_input = pandas.DataFrame
handler._sf_max_batch_size = 500

# Local testing
if __name__ == "__main__":
    from snowdev import SnowflakeConnection

    session = SnowflakeConnection().get_session()
    print(handler("test"))
