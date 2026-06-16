import psycopg2
import logging
from datetime import datetime
from os import getenv, path
from dotenv import load_dotenv

# Setup logging
log_file = path.join(path.dirname(path.abspath(__file__)), 'lazada_insert.log')
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
        # Drop existing tables if they exist
        cur.execute("""
            DROP TABLE IF EXISTS lazada_attributes, lazada_images, lazada_skus, lazada_products CASCADE
        """)
        
        # Create lazada_products table
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
        
        # Create lazada_skus table
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
        
        # Create lazada_images table
        cur.execute("""
            CREATE TABLE IF NOT EXISTS lazada_images (
                id SERIAL,
                item_id BIGINT REFERENCES lazada_products(item_id),
                image_url TEXT,
                created_date DATE DEFAULT CURRENT_DATE,
                CONSTRAINT lazada_images_pkey PRIMARY KEY (item_id, image_url)
            )
        """)
        
        # Create lazada_attributes table
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

def insert_sample_data():
    sample_data = {
        "data": {
            "total_products": 1,
            "products": [
                {
                    "created_time": "1742835004738",
                    "updated_time": "1742835004927",
                    "images": [
                        "https://vn-live.slatic.net/p/a77ab0d38776f6f72c67ad29c0743bcd.jpg",
                        "https://vn-live.slatic.net/p/fdf82d6465fb01b94023a4ad6371a171.jpg"
                    ],
                    "skus": [
                        {
                            "Status": "active",
                            "quantity": 100,
                            "SellerSku": "1234SKU",
                            "ShopSku": "3056230414_VNAMZ-14701183682",
                            "special_price": 0,
                            "price": 250000,
                            "Available": 100,
                            "SkuId": 14701183682
                        }
                    ],
                    "item_id": 3056230414,
                    "primary_category": 13156,
                    "attributes": {
                        "name": "Túi Pickleball Joola Vision II Backpack (Blue)",
                        "brand": "JOOLA",
                        "description": "<article class=\"lzd-article\" style=\"white-space:break-spaces\">Ba lô Joola Vision II Backpack là sự kết hợp hoàn hảo...</article>"
                    },
                    "status": "Active"
                }
            ]
        }
    }

    conn = None
    try:
        conn = connect_to_db()
        
        create_tables(conn)
        
        today = datetime.now().date()
        products = sample_data['data']['products']
        
        with conn.cursor() as cur:
            for product in products:
                try:
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
                        product['item_id'],
                        product['attributes']['name'],
                        product['created_time'],
                        product['updated_time'],
                        product['primary_category'],
                        product['status'],
                        today
                    ))

                    # Insert SKUs
                    if product.get('skus'):
                        # Delete existing SKUs first
                        delete_skus_sql = """
                            DELETE FROM lazada_skus
                            WHERE item_id = %s
                        """
                        cur.execute(delete_skus_sql, (product['item_id'],))
                        
                        # Insert new SKUs
                        for sku in product['skus']:
                            sku_sql = """
                                INSERT INTO lazada_skus
                                (item_id, sku_id, seller_sku, shop_sku, status, quantity, available, price, special_price, created_date)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                            """
                            cur.execute(sku_sql, (
                                product['item_id'],
                                sku['SkuId'],
                                sku['SellerSku'],
                                sku['ShopSku'],
                                sku['Status'],
                                sku['quantity'],
                                sku['Available'],
                                sku['price'],
                                sku['special_price'],
                                today
                            ))

                    # Insert images
                    if product.get('images'):
                        for image_url in product['images']:
                            image_sql = """
                                INSERT INTO lazada_images AS li
                                (item_id, image_url, created_date)
                                VALUES (%s, %s, %s)
                                ON CONFLICT (item_id, image_url) DO UPDATE SET
                                    image_url = EXCLUDED.image_url,
                                    created_date = EXCLUDED.created_date
                            """
                            cur.execute(image_sql, (
                                product['item_id'],
                                image_url,
                                today
                            ))

                    # Insert attributes
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
                            product['attributes']['brand'],
                            product['attributes']['description'],
                            today
                        ))
                        
                    conn.commit()
                    logger.info(f"Successfully inserted product {product['item_id']}")
                    
                except Exception as e:
                    logger.error(f"Error inserting product {product.get('item_id')}: {e}")
                    conn.rollback()
                    continue
                
    except Exception as e:
        logger.error(f"Error in data insertion: {e}")
        if conn:
            conn.rollback()
    finally:
        if conn:
            conn.close()

if __name__ == "__main__":
    insert_sample_data()