import pandas as pd
import io

def parse_strava_csv(csv_text: str) -> pd.DataFrame:
    # Very lenient parser; expects columns like distance, moving_time, calories, heartrate, etc.
    df = pd.read_csv(io.StringIO(csv_text))
    return df

def parse_google_fit_csv(csv_text: str) -> pd.DataFrame:
    df = pd.read_csv(io.StringIO(csv_text))
    return df
