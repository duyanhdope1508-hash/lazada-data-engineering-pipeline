from pyspark.sql import SparkSession
from pyspark.sql.functions import from_json, col, current_timestamp
from pyspark.sql.types import (
    StructType, StructField, StringType,
    IntegerType, DoubleType, ArrayType, LongType, TimestampType
)
from os import getenv
from dotenv import load_dotenv
import os
import requests

load_dotenv()

from pyspark.sql import SparkSession
import psycopg2
from pathlib import Path
import logging
from datetime import datetime

PROJECT_ROOT = Path(__file__).resolve().parents[2]
log_dir = PROJECT_ROOT / 'runtime' / 'logs'
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, f'tiki_etl_{datetime.now().strftime("%Y%m%d")}.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def create_spark_session():
    try:
        # Set Java and Hadoop home
        os.environ['JAVA_HOME'] = getenv('JAVA_HOME', r'C:\ProgramData\chocolatey\lib\jdk8\tools')
        os.environ['HADOOP_HOME'] = getenv(
            'HADOOP_HOME',
            str(PROJECT_ROOT / 'config' / 'hadoop' / 'hadoop-3.3.6')
        )
        os.environ['PATH'] = f"{Path(os.environ['HADOOP_HOME']) / 'bin'};{os.environ['PATH']}"
        hadoop_home_uri = os.environ['HADOOP_HOME'].replace('\\', '/')

        spark = SparkSession.builder \
            .appName("TikiConsumer") \
            .config("spark.jars.packages",
                    "org.apache.spark:spark-sql-kafka-0-10_2.12:3.2.0,"
                    "org.postgresql:postgresql:42.2.18,"
                    "com.datastax.spark:spark-cassandra-connector_2.12:3.2.0") \
            .config("spark.cassandra.connection.host", getenv('CASSANDRA_HOST', 'localhost')) \
            .config("spark.cassandra.connection.port", getenv('CASSANDRA_PORT', '9042')) \
            .config("spark.cassandra.auth.username", getenv('CASSANDRA_USER')) \
            .config("spark.cassandra.auth.password", getenv('CASSANDRA_PASSWORD')) \
            .config("spark.driver.host", "127.0.0.1") \
            .config("spark.driver.bindAddress", "127.0.0.1") \
            .config("spark.ui.port", "4040") \
            .config("spark.driver.memory", "2g") \
            .config("spark.executor.memory", "2g") \
            .config("spark.sql.shuffle.partitions", "2") \
            .config("spark.driver.extraJavaOptions", f"-Dhadoop.home.dir={hadoop_home_uri}") \
            .config("spark.executor.extraJavaOptions", f"-Dhadoop.home.dir={hadoop_home_uri}") \
            .master("local[*]") \
            .getOrCreate()

        spark.sparkContext.setLogLevel("WARN")
        return spark
    except Exception as e:
        logger.error(f"Failed to create Spark session: {str(e)}")
        raise


def process_stream():
    try:
        spark = create_spark_session()
        logger.info("Starting stream processing")

        hdfs_paths = [
            "hdfs://namenode:9000/data",
            "hdfs://namenode:9000/data/postgres",
            "hdfs://namenode:9000/data/postgres/lazada",
            "hdfs://namenode:9000/checkpoints"
        ]

        for path in hdfs_paths:
            spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration()) \
                .mkdirs(spark._jvm.org.apache.hadoop.fs.Path(path))

        postgres_df = spark.read \
            .format("jdbc") \
            .option("url",
                    f"jdbc:postgresql://{getenv('DB_HOST', 'localhost')}:{getenv('DB_PORT', 5433)}/{getenv('DB_NAME')}") \
            .option("driver", "org.postgresql.Driver") \
            .option("dbtable", """
                (SELECT 
                    p.item_id,
                    p.name,
                    p.created_time,
                    p.updated_time,
                    p.primary_category,
                    p.status,
                    s.sku_id,
                    s.seller_sku,
                    s.shop_sku,
                    s.status as sku_status,
                    s.quantity,
                    s.available,
                    s.price,
                    s.special_price,
                    a.brand,
                    a.description,
                    i.image_url
                FROM lazada_products p
                LEFT JOIN lazada_skus s ON p.item_id = s.item_id
                LEFT JOIN lazada_attributes a ON p.item_id = a.item_id
                LEFT JOIN lazada_images i ON p.item_id = i.item_id
                ) AS full_products
            """) \
            .option("user", getenv('DB_USER')) \
            .option("password", getenv('DB_PASSWORD')) \
            .load()

        postgres_df.write \
            .mode("overwrite") \
            .partitionBy("primary_category") \
            .parquet("hdfs://namenode:9000/data/postgres/lazada/products")

        logger.info("PostgreSQL data saved to HDFS successfully")

        postgres_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .option("keyspace", "tiki") \
            .option("table", "products") \
            .option("confirm.truncate", "false") \
            .option("spark.cassandra.output.batch.size.rows", "auto") \
            .option("spark.cassandra.output.concurrent.writes", "10") \
            .save()

        logger.info("PostgreSQL data transferred to Cassandra successfully")

        lazada_schema = StructType([

            StructField("product", StructType([
                StructField("item_id", LongType()),
                StructField("name", StringType()),
                StructField("created_time", TimestampType()),
                StructField("updated_time", TimestampType()),
                StructField("primary_category", IntegerType()),
                StructField("status", StringType())
            ])),

            StructField("skus", ArrayType(StructType([
                StructField("item_id", LongType()),
                StructField("sku_id", LongType()),
                StructField("seller_sku", StringType()),
                StructField("shop_sku", StringType()),
                StructField("status", StringType()),
                StructField("quantity", IntegerType()),
                StructField("available", IntegerType()),
                StructField("price", DoubleType()),
                StructField("special_price", DoubleType())
            ]))),

            StructField("images", ArrayType(StructType([
                StructField("item_id", LongType()),
                StructField("image_url", StringType())
            ]))),

            StructField("attributes", StructType([
                StructField("item_id", LongType()),
                StructField("brand", StringType()),
                StructField("description", StringType())
            ]))
        ])

        df = spark.readStream \
            .format("kafka") \
            .option("kafka.bootstrap.servers", f"{getenv('KAFKA_SERVERS', 'localhost:9092')}") \
            .option("subscribe", "lazada-products") \
            .option("startingOffsets", "earliest") \
            .option("failOnDataLoss", "false") \
            .load()

        parsed_df = df.select(
            from_json(col("value").cast("string"), lazada_schema).alias("data")
        ).select(
            col("data.product.item_id").alias("item_id"),
            col("data.product.name").alias("name"),
            col("data.product.created_time").alias("created_time"),
            col("data.product.updated_time").alias("updated_time"),
            col("data.product.primary_category").alias("primary_category"),
            col("data.product.status").alias("status"),
            col("data.skus")[0]["price"].alias("price"),
            col("data.skus")[0]["quantity"].alias("quantity"),
            col("data.images")[0]["image_url"].alias("image_url"),
            col("data.attributes.brand").alias("brand"),
            col("data.attributes.description").alias("description"),
            current_timestamp().alias("processing_time")
        )

        query1 = parsed_df.writeStream \
            .outputMode("append") \
            .format("parquet") \
            .option("path", "hdfs://namenode:9000/data/tiki/products") \
            .option("checkpointLocation", "hdfs://namenode:9000/checkpoints/tiki/products") \
            .start()

        query1 = parsed_df.writeStream \
            .foreachBatch(save_to_hdfs) \
            .start()

        query2 = parsed_df.writeStream \
            .foreachBatch(save_to_cassandra) \
            .start()

        query3 = parsed_df.writeStream \
            .foreachBatch(save_to_postgres) \
            .start()

        query4 = parsed_df.writeStream \
            .foreachBatch(save_to_nifi) \
            .start()

        spark.streams.awaitAnyTermination()
    except Exception as e:
        logger.error(f"Stream processing failed: {str(e)}")
        raise
    finally:
        logger.info("Stream processing ended")


def save_to_hdfs(batch_df, batch_id):
    try:
        output_path = f"hdfs://namenode:9000/data/kafka/lazada/batch_{batch_id}"

        batch_df.write \
            .mode("append") \
            .partitionBy("timestamp") \
            .parquet(output_path)

        logger.info(f"Batch {batch_id} saved to HDFS successfully")
    except Exception as e:
        logger.error(f"Failed to save batch {batch_id} to HDFS: {str(e)}")
        logger.info("Attempting to save to local storage as fallback...")

        try:
            output_dir = Path(os.path.dirname(os.path.abspath(__file__))) / '..' / 'data' / 'products'
            output_dir.mkdir(parents=True, exist_ok=True)

            batch_df.write \
                .mode("append") \
                .parquet(str(output_dir))
            logger.info(f"Batch {batch_id} saved to local parquet file")
        except Exception as local_error:
            logger.error(f"Failed to save batch {batch_id} to local storage: {local_error}")
            raise


def save_to_cassandra(batch_df, batch_id):
    try:
        batch_df = batch_df.withColumn("timestamp", col("timestamp").cast("timestamp")) \
            .withColumn("price", col("price").cast("decimal(10,2)")) \
            .withColumn("quantity", col("quantity").cast("integer"))

        batch_df.write \
            .format("org.apache.spark.sql.cassandra") \
            .mode("append") \
            .option("keyspace", "tiki") \
            .option("table", "products") \
            .option("confirm.truncate", "false") \
            .option("spark.cassandra.output.batch.size.rows", "auto") \
            .option("spark.cassandra.output.concurrent.writes", "10") \
            .save()

        logger.info(f"Batch {batch_id} saved to Cassandra successfully")
    except Exception as e:
        logger.error(f"Failed to save batch {batch_id} to Cassandra: {str(e)}")
        raise


def save_to_postgres(batch_df, batch_id):
    try:
        batch_df.write \
            .format("jdbc") \
            .mode("append") \
            .option("url",
                    f"jdbc:postgresql://{getenv('DB_HOST', 'localhost')}:{getenv('DB_PORT', 5433)}/{getenv('DB_NAME')}") \
            .option("driver", "org.postgresql.Driver") \
            .option("dbtable", "tiki_products") \
            .option("user", getenv('DB_USER')) \
            .option("password", getenv('DB_PASSWORD')) \
            .save()
        logger.info(f"Batch {batch_id} saved to PostgreSQL")
    except Exception as e:
        logger.error(f"Failed to save batch {batch_id} to PostgreSQL: {str(e)}")


def save_to_nifi(batch_df, batch_id):
    try:
        json_data = batch_df.toJSON().collect()

        nifi_url = f"http://{getenv('NIFI_HOST')}:8080/nifi-api/process-groups/root/processors"
        headers = {
            'Content-Type': 'application/json'
        }

        for record in json_data:
            response = requests.post(nifi_url, headers=headers, data=record)
            response.raise_for_status()

        logger.info(f"Batch {batch_id} sent to NiFi")
    except Exception as e:
        logger.error(f"Failed to send batch {batch_id} to NiFi: {str(e)}")


def create_hdfs_file(spark, content, hdfs_path):
    try:
        df = spark.createDataFrame([content])

        df.write \
            .mode("overwrite") \
            .text(hdfs_path)

        logger.info(f"File created successfully at {hdfs_path}")
    except Exception as e:
        logger.error(f"Failed to create file in HDFS: {str(e)}")


def write_to_hdfs(spark, content, hdfs_path):
    try:

        fs = spark._jvm.org.apache.hadoop.fs.FileSystem.get(spark._jsc.hadoopConfiguration())

        path = spark._jvm.org.apache.hadoop.fs.Path(hdfs_path)
        output_stream = fs.create(path)

        writer = spark._jvm.java.io.BufferedWriter(
            spark._jvm.java.io.OutputStreamWriter(output_stream)
        )
        writer.write(content)
        writer.close()

        logger.info(f"File written successfully to {hdfs_path}")
    except Exception as e:
        logger.error(f"Failed to write to HDFS: {str(e)}")

