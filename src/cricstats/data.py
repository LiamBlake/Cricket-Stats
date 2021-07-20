import pandas as pd
from pyreadr import read_r


def load_cleaned_rds(filename: str) -> pd.DataFrame:
    result = read_r(filename)[None]

    return result


def sequences(bbb: pd.DataFrame, window: int = 18) -> pd.DataFrame:
    pass  # for key, group in bbb.groupby([""])
