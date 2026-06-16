-- Set session parameters for better performance
SET session_replication_role = replica;  -- Temporarily disable triggers and constraints
SET maintenance_work_mem = '2GB';        -- Increase work memory for large operations
SET synchronous_commit = off;            -- Disable synchronous commit for speed
SET work_mem = '256MB';                  -- Increase working memory
SET effective_cache_size = '4GB';        -- Set cache size
SET max_parallel_workers_per_gather = 4; -- Use parallel workers

BEGIN;

-- Create temporary tables without indexes or constraints
CREATE TEMP TABLE temp_products (LIKE lazada_products INCLUDING ALL) ON COMMIT DROP;
CREATE TEMP TABLE temp_skus (LIKE lazada_skus INCLUDING ALL) ON COMMIT DROP;
CREATE TEMP TABLE temp_images (LIKE lazada_images INCLUDING ALL) ON COMMIT DROP;
CREATE TEMP TABLE temp_attributes (LIKE lazada_attributes INCLUDING ALL) ON COMMIT DROP;

-- Bulk insert into temp tables
WITH RECURSIVE numbers AS (
    SELECT generate_series(1, 500000) as n
)
INSERT INTO temp_products 
SELECT 
    nextval('lazada_products_id_seq'),
    7056230414 + n,
    'Túi Pickleball Joola Vision II Backpack (Blue) ' || n,
    to_timestamp('1742835004738'::bigint/1000),
    to_timestamp('1742835004927'::bigint/1000),
    13156,
    'Active',
    CURRENT_DATE
FROM numbers;

-- Bulk insert SKUs
WITH RECURSIVE numbers AS (
    SELECT generate_series(1, 500000) as n
)
INSERT INTO temp_skus
SELECT 
    nextval('lazada_skus_id_seq'),
    7056230414 + n,
    54701183682 + n,
    '1234SKU_' || n,
    (7056230414 + n) || '_VNAMZ-' || (54701183682 + n),
    'active',
    100,
    100,
    250000,
    0,
    CURRENT_DATE
FROM numbers;

-- Bulk insert images
WITH RECURSIVE numbers AS (
    SELECT generate_series(1, 500000) as n
)
INSERT INTO temp_images
SELECT 
    nextval('lazada_images_id_seq'),
    7056230414 + n,
    'https://picsum.photos/800/600?random=' || (n % 1000),
    CURRENT_DATE
FROM numbers
UNION ALL
SELECT 
    nextval('lazada_images_id_seq'),
    7056230414 + n,
    'https://picsum.photos/400/300?random=' || ((n % 1000) + 1000),
    CURRENT_DATE
FROM numbers;

-- Bulk insert attributes
WITH RECURSIVE numbers AS (
    SELECT generate_series(1, 500000) as n
)
INSERT INTO temp_attributes
SELECT 
    nextval('lazada_attributes_id_seq'),
    7056230414 + n,
    'JOOLA',
    CASE 
        WHEN n % 3 = 0 THEN 'Ba lô Joola Vision II Backpack màu xanh dương...' || n
        WHEN n % 3 = 1 THEN 'Túi đựng vợt Pickleball Joola Vision II...' || n
        ELSE 'Balo thể thao Joola Vision II...' || n
    END,
    CURRENT_DATE
FROM numbers;

-- Insert from temp tables to actual tables using parallel operations
INSERT INTO lazada_products SELECT * FROM temp_products;
INSERT INTO lazada_skus SELECT * FROM temp_skus;
INSERT INTO lazada_images SELECT * FROM temp_images;
INSERT INTO lazada_attributes SELECT * FROM temp_attributes;

-- Reset session parameters
SET session_replication_role = DEFAULT;
SET maintenance_work_mem = DEFAULT;
SET synchronous_commit = on;
SET work_mem = DEFAULT;
SET effective_cache_size = DEFAULT;
SET max_parallel_workers_per_gather = DEFAULT;

COMMIT;