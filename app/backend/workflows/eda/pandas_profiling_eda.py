from ydata_profiling import ProfileReport
import pandas as pd

def generate_pandas_eda_report(df: pd.DataFrame, output_file: str = "pandas_eda_report_1.html"):
    profile = ProfileReport(df, title="Automated Pandas EDA Report", explorative=True, correlations= None)
    profile.to_file(output_file)
    return output_file  # Return path for optional later us




