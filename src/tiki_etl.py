import requests
import psycopg2
import schedule
import time
import logging
from datetime import datetime
from os import getenv, path
from dotenv import load_dotenv
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider

# Setup logging
log_file = path.join(path.dirname(path.abspath(__file__)), 'tiki_etl.log')
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


def connect_to_db():
    conn = None
    try:
        conn = psycopg2.connect(
            host=getenv('DB_HOST', 'localhost'),
            port=int(getenv('DB_PORT', 5433)),
            database=getenv('DB_NAME'),
            user=getenv('DB_USER'),
            password=getenv('DB_PASSWORD'),
            connect_timeout=30
        )
        logger.info("Successfully connected to database")
        return conn
    except psycopg2.Error as e:
        logger.error(f"Database connection failed: {e}")
        if conn:
            conn.close()
        raise


def create_tables(conn):
    with conn.cursor() as cur:
        cur.execute("""
            DROP TABLE IF EXISTS lazada_attributes, lazada_images, lazada_skus, lazada_products CASCADE
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS lazada_products (
                id SERIAL,
                item_id BIGINT PRIMARY KEY,
                name VARCHAR(255),
                created_time TIMESTAMP,
                updated_time TIMESTAMP,
                primary_category INTEGER,
                status VARCHAR(50),
                created_date DATE DEFAULT CURRENT_DATE
            )
        """)

        # Create lazada_skus table with composite key
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lazada_skus (
                id SERIAL,
                item_id BIGINT REFERENCES lazada_products(item_id),
                sku_id BIGINT,
                seller_sku VARCHAR(100),
                shop_sku VARCHAR(100),
                status VARCHAR(50),
                quantity INTEGER,
                available INTEGER,
                price DECIMAL,
                special_price DECIMAL,
                created_date DATE DEFAULT CURRENT_DATE,
                CONSTRAINT lazada_skus_pkey PRIMARY KEY (item_id, sku_id)
            )
        """)

        # Create lazada_images table with composite key
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lazada_images (
                id SERIAL,
                item_id BIGINT REFERENCES lazada_products(item_id),
                image_url TEXT,
                created_date DATE DEFAULT CURRENT_DATE,
                CONSTRAINT lazada_images_pkey PRIMARY KEY (item_id, image_url)
            )
        """)

        cur.execute("""
            CREATE TABLE IF NOT EXISTS lazada_attributes (
                id SERIAL,
                item_id BIGINT REFERENCES lazada_products(item_id),
                brand VARCHAR(100),
                description TEXT,
                created_date DATE DEFAULT CURRENT_DATE,
                CONSTRAINT lazada_attributes_pkey PRIMARY KEY (item_id)
            )
        """)
    conn.commit()
    logger.info("Database tables created/verified successfully")


def fetch_tiki_data(page=1):
    url = "https://api.lazada.vn/rest/products/get"
    timestamp = str(int(time.time()))
    params = {
        "offset": (page - 1),
        "limit": 20,
        "sign": getenv('LAZADA_SIGN'),
        "app_key": getenv('LAZADA_APP_KEY'),
        "timestamp": timestamp,
        "sign_method": "sha256",
        "access_token": getenv('LAZADA_ACCESS_TOKEN'),
        "code": getenv('LAZADA_CODE')
    }

    try:
        response = requests.get(url, params=params, headers={})
        response.raise_for_status()
        data = response.json()
        logger.info(f"Successfully fetched page {page} from Lazada API")
        return data
    except requests.RequestException as e:
        logger.error(f"Error fetching data from Lazada API (page {page}): {e}")
        return None


def get_sql_type(value):
    if isinstance(value, bool):
        return "BOOLEAN"
    elif isinstance(value, int):
        return "INTEGER"
    elif isinstance(value, float):
        return "DECIMAL"
    elif isinstance(value, str):
        return "TEXT"
    elif isinstance(value, (dict, list)):
        return "JSONB"
    else:
        return "TEXT"


def create_table_from_json(conn, table_name, json_data):
    columns = []

    for key, value in json_data.items():
        sql_type = get_sql_type(value)
        columns.append(f"{key.lower()} {sql_type}")

    columns.append("created_date DATE")

    with conn.cursor() as cur:
        create_table_sql = f"""
            CREATE TABLE IF NOT EXISTS {table_name} (
                id SERIAL PRIMARY KEY,
                {', '.join(columns)}
            )
        """
        cur.execute(create_table_sql)
    conn.commit()
    logger.info(f"Table {table_name} created/verified successfully")


def process_and_save_data(run_migration=False):
    conn = None
    try:
        conn = connect_to_db()

        if run_migration:
            create_tables(conn)
            logger.info("Database migration completed")

        page = 1
        total_products = 0
        today = datetime.now().date()

        while True:
            data = fetch_tiki_data(page)
            if not data or not data.get('data', {}).get('products'):
                break

            products = data['data']['products']
            logger.info(f"Found {len(products)} products on page {page}")

            with conn.cursor() as cur:
                for product in products:
                    try:
                        # Insert into products table
                        product_sql = """
                            INSERT INTO lazada_products AS lp
                            (item_id, name, created_time, updated_time, primary_category, status, created_date)
                            VALUES (%s, %s, to_timestamp(%s::bigint/1000), to_timestamp(%s::bigint/1000), %s, %s, %s)
                            ON CONFLICT (item_id) DO UPDATE SET
                                name = EXCLUDED.name,
                                created_time = EXCLUDED.created_time,
                                updated_time = EXCLUDED.updated_time,
                                primary_category = EXCLUDED.primary_category,
                                status = EXCLUDED.status,
                                created_date = EXCLUDED.created_date
                            RETURNING item_id
                        """
                        cur.execute(product_sql, (
                            product.get('item_id'),
                            product['attributes'].get('name'),
                            product.get('created_time'),
                            product.get('updated_time'),
                            product.get('primary_category'),
                            product.get('status'),
                            today
                        ))

                        # Insert SKUs
                        if product.get('skus'):
                            for sku in product['skus']:
                                sku_sql = """
                                    INSERT INTO lazada_skus AS ls
                                    (item_id, sku_id, seller_sku, shop_sku, status, quantity, available, price, special_price, created_date)
                                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                                    ON CONFLICT (item_id, sku_id) DO UPDATE SET
                                        seller_sku = EXCLUDED.seller_sku,
                                        shop_sku = EXCLUDED.shop_sku,
                                        status = EXCLUDED.status,
                                        quantity = EXCLUDED.quantity,
                                        available = EXCLUDED.available,
                                        price = EXCLUDED.price,
                                        special_price = EXCLUDED.special_price,
                                        created_date = EXCLUDED.created_date
                                """
                                cur.execute(sku_sql, (
                                    product['item_id'],
                                    sku.get('SkuId'),
                                    sku.get('SellerSku'),
                                    sku.get('ShopSku'),
                                    sku.get('Status'),
                                    sku.get('quantity'),
                                    sku.get('Available'),
                                    sku.get('price'),
                                    sku.get('special_price'),
                                    today
                                ))

                        if product.get('images'):
                            for image_url in product['images']:
                                image_sql = """
                                    INSERT INTO lazada_images AS li
                                    (item_id, image_url, created_date)
                                    VALUES (%s, %s, %s)
                                    ON CONFLICT (item_id, image_url) DO NOTHING
                                """
                                cur.execute(image_sql, (product['item_id'], image_url, today))

                        if product.get('attributes'):
                            attr_sql = """
                                INSERT INTO lazada_attributes AS la
                                (item_id, brand, description, created_date)
                                VALUES (%s, %s, %s, %s)
                                ON CONFLICT (item_id) DO UPDATE SET
                                    brand = EXCLUDED.brand,
                                    description = EXCLUDED.description,
                                    created_date = EXCLUDED.created_date
                        """
                            cur.execute(attr_sql, (
                                product['item_id'],
                                product['attributes'].get('brand'),
                                product['attributes'].get('description'),
                                today
                            ))

                        conn.commit()
                        total_products += 1

                    except Exception as e:
                        logger.error(f"Error inserting product {product.get('item_id')}: {e}")
                        conn.rollback()
                        continue

            if len(products) < 20:
                break
            page += 1

        logger.info(f"Successfully processed {total_products} products")

    except Exception as e:
        logger.error(f"Error processing data: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()