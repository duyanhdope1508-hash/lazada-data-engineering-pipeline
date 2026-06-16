

-- Create lazada_products table
CREATE TABLE IF NOT EXISTS lazada_products (
    id SERIAL,
    item_id BIGINT PRIMARY KEY,
    name VARCHAR(255),
    created_time TIMESTAMP,
    updated_time TIMESTAMP,
    primary_category INTEGER,
    status VARCHAR(50),
    created_date DATE DEFAULT CURRENT_DATE
);

-- Create lazada_skus table
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
);

-- Create lazada_images table
CREATE TABLE IF NOT EXISTS lazada_images (
    id SERIAL,
    item_id BIGINT REFERENCES lazada_products(item_id),
    image_url TEXT,
    created_date DATE DEFAULT CURRENT_DATE,
    CONSTRAINT lazada_images_pkey PRIMARY KEY (item_id, image_url)
);

-- Create lazada_attributes table
CREATE TABLE IF NOT EXISTS lazada_attributes (
    id SERIAL,
    item_id BIGINT REFERENCES lazada_products(item_id),
    brand VARCHAR(100),
    description TEXT,
    created_date DATE DEFAULT CURRENT_DATE,
    CONSTRAINT lazada_attributes_pkey PRIMARY KEY (item_id)
);

-- Insert sample product
INSERT INTO lazada_products 
(item_id, name, created_time, updated_time, primary_category, status, created_date)
VALUES 
(3056230414, 'Túi Pickleball Joola Vision II Backpack (Blue)', 
to_timestamp('1742835004738'::bigint/1000), 
to_timestamp('1742835004927'::bigint/1000), 
13156, 'Active', CURRENT_DATE);

-- Insert SKU
INSERT INTO lazada_skus
(item_id, sku_id, seller_sku, shop_sku, status, quantity, available, price, special_price, created_date)
VALUES 
(3056230414, 14701183682, '1234SKU', '3056230414_VNAMZ-14701183682', 
'active', 100, 100, 250000, 0, CURRENT_DATE);

-- Insert images
INSERT INTO lazada_images
(item_id, image_url, created_date)
VALUES 
(3056230414, 'https://vn-live.slatic.net/p/a77ab0d38776f6f72c67ad29c0743bcd.jpg', CURRENT_DATE),
(3056230414, 'https://vn-live.slatic.net/p/fdf82d6465fb01b94023a4ad6371a171.jpg', CURRENT_DATE);

-- Insert attributes
INSERT INTO lazada_attributes
(item_id, brand, description, created_date)
VALUES 
(3056230414, 'JOOLA', 'Ba lô Joola Vision II Backpack là sự kết hợp hoàn hảo...', CURRENT_DATE);