BEGIN;

-- Insert 99 sample products first
WITH RECURSIVE numbers AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 100
)
INSERT INTO lazada_products 
(item_id, name, created_time, updated_time, primary_category, status, created_date)
SELECT 
    4056230414 + n,
    'Túi Pickleball Joola Vision II Backpack (Blue) ' || n,
    to_timestamp('1742835004738'::bigint/1000),
    to_timestamp('1742835004927'::bigint/1000),
    13156,
    'Active',
    CURRENT_DATE
FROM numbers;

-- Then insert SKUs
WITH RECURSIVE numbers AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 100
)
INSERT INTO lazada_skus
(item_id, sku_id, seller_sku, shop_sku, status, quantity, available, price, special_price, created_date)
SELECT 
    4056230414 + n,
    24701183682 + n,
    '1234SKU_' || n,
    (4056230414 + n) || '_VNAMZ-' || (24701183682 + n),
    'active',
    100,
    100,
    250000,
    0,
    CURRENT_DATE
FROM numbers;

-- Then insert images with Lorem Picsum
WITH RECURSIVE numbers AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 100
)
INSERT INTO lazada_images
(item_id, image_url, created_date)
SELECT 
    4056230414 + n,
    'https://picsum.photos/800/600?random=' || n,
    CURRENT_DATE
FROM numbers
UNION ALL
SELECT 
    4056230414 + n,
    'https://picsum.photos/400/300?random=' || (n + 100),
    CURRENT_DATE
FROM numbers;

-- Finally insert attributes
WITH RECURSIVE numbers AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 100
)
INSERT INTO lazada_attributes
(item_id, brand, description, created_date)
SELECT 
    4056230414 + n,
    'JOOLA',
    CASE 
        WHEN n % 3 = 0 THEN 'Ba lô Joola Vision II Backpack màu xanh dương, thiết kế hiện đại với nhiều ngăn tiện dụng. Chất liệu cao cấp, chống thấm nước tốt. Phù hợp cho các hoạt động thể thao và du lịch. Model ' || n
        WHEN n % 3 = 1 THEN 'Túi đựng vợt Pickleball Joola Vision II, thiết kế đặc biệt với ngăn đệm bảo vệ. Dây đeo vai có thể điều chỉnh, thoải mái khi sử dụng. Phiên bản giới hạn số ' || n
        ELSE 'Balo thể thao Joola Vision II, sản phẩm cao cấp từ thương hiệu JOOLA. Thiết kế thông minh với ngăn chứa đồ riêng biệt. Chống sốc tốt, bảo vệ trang thiết bị. Phiên bản đặc biệt ' || n
    END,
    CURRENT_DATE
FROM numbers;

COMMIT;