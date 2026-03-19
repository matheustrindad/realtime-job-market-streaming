from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, lit
from pyspark.sql.types import StructType, StructField, StringType, FloatType

spark = SparkSession.builder \
    .appName("JobMarketAnomalyDetector") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.5.0,org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

schema = StructType([
    StructField("title", StringType(), True),
    StructField("company", StringType(), True),
    StructField("location", StringType(), True),
    StructField("salary_min", FloatType(), True),
    StructField("timestamp", StringType(), True)
])

df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "job-events") \
    .load()

parsed_df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .na.fill(0, ["salary_min"])

anomalies_df = parsed_df.withColumn(
    "is_anomaly",
    when(col("salary_min") > 1000, lit(True)).otherwise(lit(False))
)

def save_to_postgres(batch_df, batch_id):
    batch_df.write \
        .format("jdbc") \
        .option("url", "jdbc:postgresql://db:5432/job_market") \
        .option("dbtable", "job_events") \
        .option("user", "user") \
        .option("password", "password") \
        .option("driver", "org.postgresql.Driver") \
        .mode("append") \
        .save()
    print(f">>> Batch {batch_id} saved — {batch_df.count()} rows")

query = anomalies_df.writeStream \
    .outputMode("append") \
    .foreachBatch(save_to_postgres) \
    .start()

query.awaitTermination()