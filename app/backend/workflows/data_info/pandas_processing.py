import pandas as pd

def get_dataset_info(file_path):
    df = pd.read_csv(file_path)
    info = {
        "rows": df.shape[0],
        "columns": df.shape[1],
        "memory_usage_mb": df.memory_usage(deep=True).sum() / (1024 * 1024),
        "columns_names": df.columns.tolist(),
        "null_counts": df.isnull().sum().to_dict()
    }
    return info
