import os
import pandas as pd
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import LabelEncoder, StandardScaler


UPLOAD_DIR = "/home/master_node/Gensight_P/uploaded_files"
def drop_columns(df: pd.DataFrame, cols_to_drop: list) -> pd.DataFrame:
    cols_exist = [col for col in cols_to_drop if col in df.columns]
    return df.drop(columns=cols_exist)

def impute_missing_values(df: pd.DataFrame) -> pd.DataFrame:
    # Separate numeric and categorical columns
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    categorical_cols = df.select_dtypes(include=['object']).columns

    # Impute numeric with mean
    if len(numeric_cols) > 0:
        num_imputer = SimpleImputer(strategy='mean')
        df[numeric_cols] = num_imputer.fit_transform(df[numeric_cols])

    # Impute categorical with most frequent
    if len(categorical_cols) > 0:
        cat_imputer = SimpleImputer(strategy='most_frequent')
        df[categorical_cols] = cat_imputer.fit_transform(df[categorical_cols])

    return df

def label_encode_columns(df: pd.DataFrame, label_encode_cols: list) -> pd.DataFrame:
    for col in label_encode_cols:
        if col in df.columns:
            le = LabelEncoder()
            df[col] = le.fit_transform(df[col].astype(str))
    return df

def apply_standard_scaling(df: pd.DataFrame) -> pd.DataFrame:
    numeric_cols = df.select_dtypes(include=['float64', 'int64']).columns
    if len(numeric_cols) == 0:
        return df

    scaler = StandardScaler()
    df[numeric_cols] = scaler.fit_transform(df[numeric_cols])
    return df

def drop_empty_columns(df: pd.DataFrame, threshold: float = 1.0) -> pd.DataFrame:
    # threshold=1.0 means drop columns where 100% values are missing
    missing_ratio = df.isna().mean()
    cols_to_drop = missing_ratio[missing_ratio >= threshold].index.tolist()
    if cols_to_drop:
        print(f"Dropping empty columns: {cols_to_drop}")
    return df.drop(columns=cols_to_drop)

def clean_data(df: pd.DataFrame, cleaning_instructions: dict) -> pd.DataFrame:
    # Drop columns
    if 'drop_columns' in cleaning_instructions:
        df = drop_columns(df, cleaning_instructions['drop_columns'])
    
    # Drop columns that have 100% missing values (to avoid imputer errors)
    df = drop_empty_columns(df, threshold=1.0)

    # Impute missing values
    df = impute_missing_values(df)

    # Label encode
    # if 'label_encoding' in cleaning_instructions:
    #     df = label_encode_columns(df, cleaning_instructions['label_encoding'])

    # Standard scaling
    if cleaning_instructions.get('standard_scalar', ['no'])[0].lower() == 'yes':
        # Only scale feature columns, skip target for classification
        problem_type = cleaning_instructions.get('problem_type', ['regression'])[0].lower()
        target_col = cleaning_instructions.get('target_column', [None])[0]
        print(target_col)
        if problem_type == 'classification' and target_col in df.columns:
            feature_cols = [c for c in df.columns if c != target_col]
            print(feature_cols)
            df[feature_cols] = apply_standard_scaling(df[feature_cols])
        else:
            df = apply_standard_scaling(df)
            print("all---------------------")
 
    return df

def save_cleaned_data(df: pd.DataFrame, filename: str = "data.csv") -> None:
    output_path = os.path.join(UPLOAD_DIR, filename)
    df.to_csv(output_path, index=False)
    return output_path





