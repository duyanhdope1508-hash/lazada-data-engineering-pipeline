import logging
import time
import schedule
import os
from pathlib import Path
from dotenv import load_dotenv
from kafka_producer.tiki_producer import send_to_kafka
from spark_consumer.tiki_consumer import process_stream
from tiki_etl import process_and_save_data
import threading

PROJECT_ROOT = Path(__file__).resolve().parents[1]

os.environ['HADOOP_HOME'] = os.getenv(
    'HADOOP_HOME',
    str(PROJECT_ROOT / 'config' / 'hadoop' / 'hadoop-3.3.6')
)
os.environ['HADOOP_CONF_DIR'] = os.getenv(
    'HADOOP_CONF_DIR',
    str(Path(os.environ['HADOOP_HOME']) / 'etc' / 'hadoop')
)
os.environ['PATH'] = f"{Path(os.environ['HADOOP_HOME']) / 'bin'};{os.environ['PATH']}"
os.environ['SPARK_LOCAL_DIRS'] = os.getenv(
    'SPARK_LOCAL_DIRS',
    str(PROJECT_ROOT / 'runtime' / 'spark_temp')
)
os.environ['HADOOP_USER_NAME'] = os.getenv('HADOOP_USER_NAME', 'root')
os.environ['HADOOP_OPTS'] = os.getenv('HADOOP_OPTS', '-Djava.net.preferIPv4Stack=true')
os.environ['CORE_SITE_CONFIGURATION'] = os.getenv('CORE_SITE_CONFIGURATION', """<?xml version="1.0" encoding="UTF-8"?>
<?xml-stylesheet type="text/xsl" href="configuration.xsl"?>
<configuration>
    <property>
        <name>fs.defaultFS</name>
        <value>hdfs://localhost:9000</value>
    </property>
</configuration>""")

Path(os.environ['SPARK_LOCAL_DIRS']).mkdir(parents=True, exist_ok=True)
Path(os.environ['HADOOP_CONF_DIR']).mkdir(parents=True, exist_ok=True)
Path(os.environ['HADOOP_HOME'], 'bin').mkdir(parents=True, exist_ok=True)

with open(Path(os.environ['HADOOP_CONF_DIR']) / 'core-site.xml', 'w') as f:
    f.write(os.environ['CORE_SITE_CONFIGURATION'])

log_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
os.makedirs(log_dir, exist_ok=True)

log_file = os.path.join(log_dir, 'main.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(log_file),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

load_dotenv()


def run_etl():
    try:
        logger.info("Starting ETL process")
        process_and_save_data(run_migration=False)
        logger.info("ETL process completed")
    except Exception as e:
        logger.error(f"ETL process failed: {e}")


def run_kafka_pipeline():
    try:
        logger.info("Starting Kafka producer")
        batch_size = 10
        send_to_kafka(batch_size=batch_size)
        logger.info("Kafka producer completed")
    except Exception as e:
        logger.error(f"Kafka producer failed: {e}")


def run_spark_pipeline():
    try:
        logger.info("Starting Spark consumer")
        time.sleep(10)

        process_stream()
        logger.info("Spark consumer completed")
    except Exception as e:
        logger.error(f"Spark consumer failed: {e}")
        for i in range(3):
            try:
                logger.info(f"Retrying Spark consumer (attempt {i + 1})")
                time.sleep(15)
                process_stream()
                logger.info("Spark consumer completed after retry")
                break
            except Exception as retry_e:
                logger.error(f"Retry {i + 1} failed: {retry_e}")


def run_pipeline():
    try:
        logger.info("Starting complete pipeline")

        logger.info("Starting Spark consumer thread")
        spark_thread = threading.Thread(target=run_spark_pipeline)
        spark_thread.daemon = True
        spark_thread.start()

        time.sleep(30)

        logger.info("Starting Kafka producer")
        run_kafka_pipeline()

        time.sleep(30)

        logger.info("Starting ETL process")
        run_etl()

        spark_thread.join(timeout=900)

        logger.info("Pipeline execution completed")
    except Exception as e:
        logger.error(f"Pipeline execution failed: {e}")


def init_database():
    try:
        logger.info("Initializing database tables")
        process_and_save_data(run_migration=True)
        logger.info("Database initialization completed")
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise


def main():
    logger.info("Starting Data Pipeline")

    init_database()

    schedule.every(60).minutes.do(run_pipeline)
    try:
        run_pipeline()
        while True:
            schedule.run_pending()
            time.sleep(60)
    except KeyboardInterrupt:
        logger.info("Pipeline stopped by user")
    except Exception as e:
        logger.error(f"Unexpected error: {e}")
        raise


if __name__ == "__main__":
    main()
