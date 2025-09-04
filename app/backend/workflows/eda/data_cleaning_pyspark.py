from pyspark.sql import DataFrame
from pyspark.sql.functions import col
from pyspark.ml.feature import StringIndexer, StandardScaler, VectorAssembler, Imputer
from pyspark.ml import Pipeline
import subprocess

def drop_columns_spark(df: DataFrame, cols_to_drop: list) -> DataFrame:
    """
    Drop specified columns if they exist in the dataframe.
    """
    cols_exist = [c for c in cols_to_drop if c in df.columns]
    if cols_exist:
        df = df.drop(*cols_exist)
    return df

def drop_empty_columns_spark(df: DataFrame, threshold: float = 1.0) -> DataFrame:
    """
    Drop columns with missing fraction >= threshold (default 1.0 means 100% missing).
    """
    total_rows = df.count()
    cols_to_drop = []
    for col_name in df.columns:
        missing_count = df.filter(col(col_name).isNull()).count()
        missing_ratio = missing_count / total_rows if total_rows > 0 else 0
        if missing_ratio >= threshold:
            cols_to_drop.append(col_name)
    if cols_to_drop:
        print(f"Dropping empty columns: {cols_to_drop}")
        df = df.drop(*cols_to_drop)
    return df

from pyspark.sql import DataFrame
from pyspark.ml.feature import Imputer

def impute_missing_spark(df: DataFrame) -> DataFrame:
    numeric_cols = [f.name for f in df.schema.fields if f.dataType.simpleString() in ['int', 'double', 'long', 'float']]
    if numeric_cols:
        imputer = Imputer(strategy="mean", inputCols=numeric_cols, outputCols=numeric_cols)
        df = imputer.fit(df).transform(df)

    categorical_cols = [f.name for f in df.schema.fields if f.dataType.simpleString() == 'string']
    for c in categorical_cols:
        mode_row = df.groupBy(c).count().orderBy('count', ascending=False).limit(1).collect()

        print(f"Imputing column '{c}': mode_row = {mode_row}")

        if mode_row and len(mode_row) > 0:
            if mode_row[0] and len(mode_row[0]) > 0 and mode_row[0][0] is not None:
                mode_value = mode_row[0][0]
            else:
                mode_value = 'missing'
        else:
            print(f"Warning: No mode found for column '{c}', using 'missing'")
            mode_value = 'missing'

        print(f"Filling column '{c}' missing values with: {mode_value}")
        df = df.fillna({c: mode_value})

    return df


def label_encode_spark(df: DataFrame, label_encode_cols: list) -> DataFrame:
    """
    Apply StringIndexer label encoding to specified columns.
    """
    stages = []
    for c in label_encode_cols:
        if c in df.columns:
            indexer = StringIndexer(inputCol=c, outputCol=f"{c}_indexed", handleInvalid="keep")
            stages.append(indexer)

    if not stages:
        return df

    pipeline = Pipeline(stages=stages)
    model = pipeline.fit(df)
    df = model.transform(df)

    # Drop original columns and rename indexed columns
    for c in label_encode_cols:
        orig_col = c
        indexed_col = f"{c}_indexed"
        if orig_col in df.columns and indexed_col in df.columns:
            df = df.drop(orig_col).withColumnRenamed(indexed_col, orig_col)
    return df

def standard_scale_spark(df: DataFrame) -> DataFrame:
    """
    Apply standard scaling (zero mean, unit variance) to numeric columns.
    """
    numeric_cols = [f.name for f in df.schema.fields if f.dataType.simpleString() in ['int', 'double', 'long', 'float']]

    if not numeric_cols:
        return df

    assembler = VectorAssembler(inputCols=numeric_cols, outputCol="features_vector")
    scaler = StandardScaler(inputCol="features_vector", outputCol="scaled_features", withMean=True, withStd=True)

    pipeline = Pipeline(stages=[assembler, scaler])
    model = pipeline.fit(df)
    df = model.transform(df)

    # Drop original numeric cols
    df = df.drop(*numeric_cols)

    # Extract scaled features back into individual columns
    from pyspark.sql.functions import udf
    from pyspark.sql.types import DoubleType

    def vector_to_columns(df, vec_col, cols):
        for i, c in enumerate(cols):
            get_element = udf(lambda v: float(v[i]) if v else None, DoubleType())
            df = df.withColumn(c, get_element(col(vec_col)))
        return df

    df = vector_to_columns(df, "scaled_features", numeric_cols)
    df = df.drop("features_vector", "scaled_features")
    return df

def clean_data_spark(df: DataFrame, instructions: dict) -> DataFrame:
    """
    Clean Spark DataFrame based on instructions dictionary.
    """
    if 'drop_columns' in instructions:
        df = drop_columns_spark(df, instructions['drop_columns'])

    df = drop_empty_columns_spark(df)

    df = impute_missing_spark(df)

    if 'label_encoding' in instructions:
        df = label_encode_spark(df, instructions['label_encoding'])

    if instructions.get('standard_scalar', ['no'])[0].lower() == 'yes':
        df = standard_scale_spark(df)

    return df

import subprocess

def save_cleaned_spark(df: DataFrame, hdfs_file_path: str):
    """
    Save Spark DataFrame as a single CSV file with exact filename on HDFS.

    Args:
        df: Spark DataFrame to save.
        hdfs_file_path: Full HDFS file path including filename (e.g. /user/gen_sight/uploads/data.csv).
    """
    import os

    # Extract directory and filename
    hdfs_dir = os.path.dirname(hdfs_file_path)
    filename = os.path.basename(hdfs_file_path)

    # Temporary directory to write single CSV part file
    tmp_dir = hdfs_dir.rstrip('/') + "_tmp_save_dir"

    # 1. Write DataFrame as single partition CSV to temp dir
    df.coalesce(1).write.mode("overwrite").option("header", "true").csv(tmp_dir)

    # 2. Find the part file in temp dir
    cmd_ls = ["hdfs", "dfs", "-ls", tmp_dir]
    proc = subprocess.run(cmd_ls, capture_output=True, text=True, check=True)
    files = [line.split()[-1] for line in proc.stdout.strip().split('\n') if line]
    part_file = next((f for f in files if "part-" in f and f.endswith(".csv")), None)

    if not part_file:
        raise RuntimeError("No part file found in temporary HDFS directory.")

    # 3. Move the part file to desired exact filename in target directory
    cmd_mv = ["hdfs", "dfs", "-mv", part_file, hdfs_file_path]
    subprocess.run(cmd_mv, check=True)

    # 4. Remove temporary directory
    cmd_rm = ["hdfs", "dfs", "-rm", "-r", tmp_dir]
    subprocess.run(cmd_rm, check=True)

    print(f"Saved cleaned DataFrame as {hdfs_file_path} on HDFS.")


