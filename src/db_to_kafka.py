import psycopg2
from kafka import KafkaProducer
import json
from os import getenv
from dotenv import load_dotenv
import logging
from datetime import datetime, date
from decimal import Decimal

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

load_dotenv()


def connect_to_db():
    try:
        conn = psycopg2.connect(
            host=getenv('DB_HOST', 'localhost'),
            port=int(getenv('DB_PORT', 5433)),
            database=getenv('DB_NAME'),
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD'),
            connect_timeout=300,  # Increased from 30 to 300 seconds
            keepalives=1,
            keepalives_idle=60,
            keepalives_interval=10,
            keepalives_count=5
        )
        logger.info("Successfully connected to database")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        raise


def create_kafka_producer():
    try:
        # Custom JSON serializer to handle datetime and decimal objects
        def json_serializer(obj):
            if isinstance(obj, (datetime, date)):
                return obj.isoformat()
            if isinstance(obj, Decimal):
                return float(obj)
            raise TypeError(f"Type {type(obj)} not serializable")

        producer = KafkaProducer(
            bootstrap_servers=getenv('KAFKA_BROKERS', 'localhost:9092'),
            value_serializer=lambda v: json.dumps(v, default=json_serializer).encode('utf-8'),
            request_timeout_ms=300000,  # 5 minutes timeout
            max_block_ms=300000  # 5 minutes timeout
        )
        logger.info("Kafka producer created successfully")
        return producer
    except Exception as e:
        logger.error(f"Failed to create Kafka producer: {e}")
        raise


def fetch_and_send_data():
    conn = None
    producer = None

    try:
        # Connect to both database and Kafka
        conn = connect_to_db()
        producer = create_kafka_producer()

        # Fetch data from database
        with conn.cursor() as cur:
            # Fetch all tables data
            cur.execute("""
                SELECT * FROM lazada_products;
            """)
            products = cur.fetchall()

            cur.execute("""
                SELECT * FROM lazada_skus;
            """)
            skus = cur.fetchall()

            cur.execute("""
                SELECT * FROM lazada_images;
            """)
            images = cur.fetchall()

            cur.execute("""
                SELECT * FROM lazada_attributes;
            """)
            attributes = cur.fetchall()

        # Prepare data for Kafka
        data = {
            'products': products,
            'skus': skus,
            'images': images,
            'attributes': attributes
        }

        # Send to Kafka
        producer.send(getenv('KAFKA_TOPIC', 'lazada_data'), value=data)
        producer.flush()
        logger.info("Data successfully sent to Kafka")

    except Exception as e:
        logger.error(f"Error in data transfer: {e}")
    finally:
        if conn:
            conn.close()
        if producer:
            producer.close()


if __name__ == "__main__":
    fetch_and_send_data()