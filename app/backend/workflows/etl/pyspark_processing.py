from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("GenSightProcessing") \
    .master("local[*]") \
    .config("spark.driver.bindAddress", "127.0.0.1") \
    .getOrCreate()


def get_dataset_info(hdfs_path):
    spark = SparkSession.builder.appName("GenSightProcessing").getOrCreate()
    df = spark.read.csv(hdfs_path, header=True, inferSchema=True)

    rows = df.count()
    columns = len(df.columns)
    columns_names = df.columns

    # Memory usage not as straightforward, skip or estimate
    null_counts = {}
    for c in columns_names:
        null_counts[c] = df.filter(df[c].isNull()).count()

    spark.stop()
    
    return {
        "rows": rows,
        "columns": columns,
        "columns_names": columns_names,
        "null_counts": null_counts
    }

