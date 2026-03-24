from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, when, lit, current_timestamp, avg
from pyspark.sql.types import StructType, StructField, StringType, FloatType
import uuid

# 1. Primeiro: Inicializa a Sessão Spark
spark = SparkSession.builder \
    .appName("JobMarketAnomalyDetector") \
    .config("spark.jars.packages", "org.apache.spark:spark-sql-kafka-0-10_2.12:3.4.0,org.postgresql:postgresql:42.6.0") \
    .getOrCreate()

spark.sparkContext.setLogLevel("ERROR")

# 2. Define o Schema e as Configurações
schema = StructType([
    StructField("title", StringType(), True),
    StructField("company", StringType(), True),
    StructField("location", StringType(), True),
    StructField("salary_min", FloatType(), True),
    StructField("timestamp", StringType(), True)
])

# 3. Define a função de processamento (Batch)
def process_batch(batch_df, batch_id):
    if batch_df.isEmpty():
        return

    avg_row = batch_df.select(avg("salary_min")).first()
    current_avg = avg_row[0] if avg_row and avg_row[0] is not None else 0

    batch_with_stats = batch_df.withColumn(
        "is_anomaly",
        when((col("salary_min") > (current_avg * 3)) & (col("salary_min") > 1000), lit(True))
        .otherwise(lit(False))
    )

    valid_df = batch_with_stats.filter(col("salary_min") >= 0)
    dlq_df = batch_with_stats.filter((col("salary_min") < 0) | (col("salary_min").isNull()))

    if not valid_df.isEmpty():
        valid_df.drop("event_time").write \
            .format("jdbc") \
            .option("url", "jdbc:postgresql://db:5432/job_market") \
            .option("dbtable", "job_events") \
            .option("user", "user") \
            .option("password", "password") \
            .option("driver", "org.postgresql.Driver") \
            .mode("append") \
            .save()

        anomalies = valid_df.filter(col("is_anomaly") == True)
        for row in anomalies.collect():
            print(f"⚠️  ANOMALY: {row['title']} - ${row['salary_min']} (Média: ${current_avg:.2f})")

    if not dlq_df.isEmpty():
        dlq_df.selectExpr("CAST(NULL AS STRING) as key", "to_json(struct(*)) as value") \
            .write \
            .format("kafka") \
            .option("kafka.bootstrap.servers", "kafka:9092") \
            .option("topic", "job-events-dlq") \
            .save()
        print(f"❌ DLQ: {dlq_df.count()} registros inválidos enviados!")

    print(f">>> Lote {batch_id} finalizado: {valid_df.count()} no DB | Média: ${current_avg:.2f}")

# 4. Lê o Stream do Kafka
df = spark.readStream \
    .format("kafka") \
    .option("kafka.bootstrap.servers", "kafka:9092") \
    .option("subscribe", "job-events") \
    .load()

parsed_df = df.selectExpr("CAST(value AS STRING)") \
    .select(from_json(col("value"), schema).alias("data")) \
    .select("data.*") \
    .na.fill(0, ["salary_min"]) \
    .withColumn("event_time", current_timestamp())

# 5. Configura o Checkpoint Dinâmico e Inicia
checkpoint_dir = f"/tmp/spark-checkpoint-{uuid.uuid4()}"

query = parsed_df.writeStream \
    .foreachBatch(process_batch) \
    .option("checkpointLocation", checkpoint_dir) \
    .start()

query.awaitTermination()