
import requests
import pandas as pd
import re
from dotenv import load_dotenv
import os

load_dotenv()
API_KEY = os.getenv("PERPLEXITY_API_KEY_1")
API_URL = "https://api.perplexity.ai/chat/completions"

def create_eda_summary_prompt(df: pd.DataFrame) -> str:
    summary = [
        "Data Types:\n" + df.dtypes.to_string(),
        "\nMissing Values:\n" + df.isnull().sum().to_string(),
        "\nUnique Values:\n" + df.nunique().to_string(),
        "\nSample Data:\n" + df.head(5).to_string()
    ]
    prompt = "\n".join(summary)
    return (
        f"Here is a basic EDA summary and sample data:\n{prompt}\n"
        "Only respond with EXACTLY the following dictionary format, no extra text:\n\n"
        "drop_columns = [col_names as a list]\n"
        "problem_type = ['classification' or 'regression']\n"
        "label_encoding = [only categorical (non-numeric/string/object) column names as a list. Do NOT include integer or float columns.]\n"
        "standard_scalar = ['yes' or 'no']\n"
        "target_column = [col_name]\n\n"
        "For example:\n"
        "drop_columns = ['col1', 'col2']\n"
        "problem_type = ['classification']\n"
        "label_encoding = ['gender']\n"
        "standard_scalar = ['yes']\n"
        "target_column = [col_name]\n\n" 
        "Only provide this. Do not explain, or add sentences."
    )


def call_gpt_api(prompt: str) -> str:
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": "sonar-pro",
        "messages": [
            {"role": "user", "content": prompt}
        ],
        "temperature": 0
    }
    response = requests.post(API_URL, json=payload, headers=headers)
    response.raise_for_status()
    data = response.json()
    return data["choices"][0]["message"]["content"]


def parse_gpt_structured_response(response_text: str) -> dict:
    # Prepare regex patterns for each expected key
    patterns = {
        "drop_columns": r"drop_columns\s*=\s*\[([^\]]*)\]",
        "problem_type": r"problem_type\s*=\s*\[([^\]]*)\]",
        "label_encoding": r"label_encoding\s*=\s*\[([^\]]*)\]",
        "standard_scalar": r"standard_scalar\s*=\s*\[([^\]]*)\]",
        "target_column": r"target_column\s*=\s*\[([^\]]*)\]",
    }
    result = {}
    for key, pattern in patterns.items():
        match = re.search(pattern, response_text, re.IGNORECASE)
        if match:
            # Split values by comma, strip quotes and whitespace
            raw_vals = match.group(1)
            vals = [v.strip().strip("\"'") for v in raw_vals.split(",") if v.strip()]
            result[key] = vals
        else:
            result[key] = []

    return result

def create_eda_summary_prompt_spark(sdf):
    """
    Create a summary prompt string for GPT from a PySpark DataFrame.
    """
    # Data Types
    data_types = "\n".join([f"{name}: {dtype}" for name, dtype in sdf.dtypes])

    # Missing Values per column
    missing_counts = {}
    total_rows = sdf.count()
    for col_name in sdf.columns:
        missing_count = sdf.filter(sdf[col_name].isNull()).count()
        missing_counts[col_name] = missing_count
    missing_str = "\n".join([f"{col}: {missing_counts[col]}" for col in sdf.columns])

    # Unique Values (approximate count distinct)
    unique_counts = {}
    for col_name in sdf.columns:
        unique_counts[col_name] = sdf.agg({col_name: "approx_count_distinct"}).collect()[0][0]
    unique_str = "\n".join([f"{col}: {unique_counts[col]}" for col in sdf.columns])

    # Sample Data (convert top 5 rows to Pandas then to string)
    sample_data = sdf.limit(5).toPandas().to_string(index=False)

    summary = (
        f"Data Types:\n{data_types}\n\n"
        f"Missing Values:\n{missing_str}\n\n"
        f"Unique Values:\n{unique_str}\n\n"
        f"Sample Data:\n{sample_data}"
    )

    prompt = (
        f"Here is a basic EDA summary and sample data:\n{summary}\n"
        "Only respond with EXACTLY the following dictionary format, no extra text:\n\n"
        "drop_columns = [col_names as a list]\n"
        "problem_type = ['classification' or 'regression']\n"
        "label_encoding = [only categorical (non-numeric/string/object) column names as a list. Do NOT include integer or float columns.]\n"
        "standard_scalar = ['yes' or 'no']\n"
        "target_column = [col_name]\n\n"
        "For example:\n"
        "drop_columns = ['col1', 'col2']\n"
        "problem_type = ['classification']\n"
        "label_encoding = ['gender','city']\n"
        "standard_scalar = ['yes']\n"
        "target_column = ['target_col']\n\n"
        "Only provide this. Do not explain, or add sentences."
    )
    return prompt


