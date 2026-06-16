-- Create keyspace if not exists
CREATE KEYSPACE IF NOT EXISTS lazada_store 
WITH replication = {
    'class': 'SimpleStrategy',
    'replication_factor': 1
};

USE lazada_store;

-- Create products table
CREATE TABLE IF NOT EXISTS products (
    item_id bigint,
    name text,
    created_time timestamp,
    updated_time timestamp,
    primary_category int,
    status text,
    created_date date,
    PRIMARY KEY (item_id)
);

-- Create SKUs table
-- Using composite key for better data distribution
CREATE TABLE IF NOT EXISTS skus (
    item_id bigint,
    sku_id bigint,
    seller_sku text,
    shop_sku text,
    status text,
    quantity int,
    available int,
    price decimal,
    special_price decimal,
    created_date date,
    PRIMARY KEY ((item_id), sku_id)
);

-- Create images table
-- Using clustering key for multiple images per item
CREATE TABLE IF NOT EXISTS images (
    item_id bigint,
    image_url text,
    created_date date,
    PRIMARY KEY ((item_id), image_url)
);

-- Create attributes table
CREATE TABLE IF NOT EXISTS attributes (
    item_id bigint,
    brand text,
    description text,
    created_date date,
    PRIMARY KEY (item_id)
);

-- Insert sample data
INSERT INTO products (
    item_id, name, created_time, updated_time, primary_category, status, created_date
) VALUES (
    3056230414,
    'Túi Pickleball Joola Vision II Backpack (Blue)',
    '2025-03-21 12:23:24',
    '2025-03-21 12:23:24',
    13156,
    'Active',
    '2024-01-01'
);

INSERT INTO skus (
    item_id, sku_id, seller_sku, shop_sku, status, quantity, available, price, special_price, created_date
) VALUES (
    3056230414,
    14701183682,
    '1234SKU',
    '3056230414_VNAMZ-14701183682',
    'active',
    100,
    100,
    250000,
    0,
    '2024-01-01'
);

INSERT INTO images (
    item_id, image_url, created_date
) VALUES (
    3056230414,
    'https://vn-live.slatic.net/p/a77ab0d38776f6f72c67ad29c0743bcd.jpg',
    '2024-01-01'
);

INSERT INTO images (
    item_id, image_url, created_date
) VALUES (
    3056230414,
    'https://vn-live.slatic.net/p/fdf82d6465fb01b94023a4ad6371a171.jpg',
    '2024-01-01'
);

INSERT INTO attributes (
    item_id, brand, description, created_date
) VALUES (
    3056230414,
    'JOOLA',
    'Ba lô Joola Vision II Backpack là sự kết hợp hoàn hảo...',
    '2024-01-01'
);