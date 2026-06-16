import json
import requests
import time
import logging
from kafka import KafkaProducer
from datetime import datetime
from os import getenv, path
from dotenv import load_dotenv
import psycopg2

log_file = path.join(path.dirname(path.abspath(__file__)), 'tiki_producer.log')
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[logging.FileHandler(log_file), logging.StreamHandler()]
)
logger = logging.getLogger(__name__)

load_dotenv()


def create_kafka_producer():
    return KafkaProducer(
        bootstrap_servers=getenv('KAFKA_SERVERS', 'localhost:9092'),
        value_serializer=lambda v: json.dumps(v).encode('utf-8')
    )


def fetch_tiki_data(page=1):
    url = "https://api.lazada.vn/rest/products/get"
    timestamp = str(int(time.time()))
    params = {
        "offset": (page - 1) * 20,
        "limit": 20,
        "sign": getenv('LAZADA_SIGN'),
        "app_key": getenv('LAZADA_APP_KEY'),
        "timestamp": timestamp,
        "sign_method": "sha256",
        "access_token": getenv('LAZADA_ACCESS_TOKEN'),
        "code": f"{getenv('LAZADA_CODE')}"
    }

    try:
        response = requests.get(url, params=params, headers={})  # Removed headers as auth is in params
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched page {page} from Lazada API")
        return data
    except requests.RequestException as e:
        logger.error(f"Error fetching data from Lazada API (page {page}): {e}")
        return None


def fetch_from_postgres():
    conn = None
    try:
        conn = psycopg2.connect(
            host=getenv('DB_HOST', 'localhost'),
            port=int(getenv('DB_PORT', 5433)),
            database=getenv('DB_NAME'),
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD')
        )

        with conn.cursor() as cur:
            cur.execute("""
                SELECT 
                    p.item_id,
                    p.name,
                    p.created_time,
                    p.updated_time,
                    p.primary_category,
                    p.status,
                    array_agg(DISTINCT i.image_url) as images,
                    jsonb_agg(
                        DISTINCT jsonb_build_object(
                            'SkuId', s.sku_id,
                            'SellerSku', s.seller_sku,
                            'ShopSku', s.shop_sku,
                            'Status', s.status,
                            'quantity', s.quantity,
                            'Available', s.available,
                            'price', s.price,
                            'special_price', s.special_price
                        )
                    ) as skus,
                    jsonb_build_object(
                        'name', p.name,
                        'brand', a.brand,
                        'description', a.description
                    ) as attributes
                FROM lazada_products p
                LEFT JOIN lazada_images i ON p.item_id = i.item_id
                LEFT JOIN lazada_skus s ON p.item_id = s.item_id
                LEFT JOIN lazada_attributes a ON p.item_id = a.item_id
                GROUP BY p.item_id, p.name, p.created_time, p.updated_time, 
                         p.primary_category, p.status, a.brand, a.description
            """)

            return cur.fetchall()
    except Exception as e:
        logger.error(f"Error fetching data from PostgreSQL: {e}")
        return None
    finally:
        if conn:
            conn.close()


def send_to_kafka(batch_size=10):
    producer = create_kafka_producer()
    current_batch = []
    total_products = 0

    try:
        products = fetch_from_postgres()
        if not products:
            logger.error("No products found in database")
            return

        for product in products:
            transformed_data = {
                'id': str(product[0]),  # item_id
                'name': product[1],
                'created_time': product[2].isoformat() if product[2] else None,
                'updated_time': product[3].isoformat() if product[3] else None,
                'primary_category': product[4],
                'status': product[5],
                'images': product[6] if product[6] else [],
                'skus': product[7] if product[7] else [],
                'attributes': product[8] if product[8] else {}
            }

            current_batch.append({
                'timestamp': datetime.now().isoformat(),
                'data': transformed_data
            })

            if len(current_batch) >= batch_size:
                for item in current_batch:
                    producer.send('tiki-products', value=item)
                producer.flush()
                logger.info(f"Sent batch of {len(current_batch)} products")
                current_batch = []

            total_products += 1

        if current_batch:
            for item in current_batch:
                producer.send('tiki-products', value=item)
            producer.flush()
            logger.info(f"Sent final batch of {len(current_batch)} products")

        logger.info(f"Sent total of {total_products} products to Kafka")
    except Exception as e:
        logger.error(f"Error sending data to Kafka: {e}")
    finally:
        producer.close()
