from pyspark.sql import functions as F


def pyspark_eda(sdf):
    print("Shape (approx):", sdf.count(), "rows,", len(sdf.columns), "columns")
    print("Columns:", sdf.columns)
    print("\nSchema:")
    sdf.printSchema()
    print("\nMissing values per column:")
    sdf.select([F.count(F.when(F.col(c).isNull(), c)).alias(c) for c in sdf.columns]).show()
    print("\nSample data:")
    sdf.show(5)
    print("\nSummary Statistics:")
    sdf.describe().show()
    # Unique values
    for c in sdf.columns:
        print(f"{c}: {sdf.select(c).distinct().count()} unique values")
    # Correlations (example)
    num_cols = [c for c, t in sdf.dtypes if t in ("double", "int")]
    if len(num_cols) >= 2:
        for i in range(len(num_cols)-1):
            corr = sdf.stat.corr(num_cols[i], num_cols[i+1])
            print(f"Correlation between {num_cols[i]} & {num_cols[i+1]}: {corr}")

# Use like:
# pyspark_eda(spark_df)  # where spark_df is your PySpark DataFrame
