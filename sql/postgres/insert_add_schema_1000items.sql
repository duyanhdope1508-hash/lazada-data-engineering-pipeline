ROLLBACK;  -- Add this line to clear any failed transaction
BEGIN;
-- Insert 1000 sample products first
WITH RECURSIVE numbers AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 1001
)
INSERT INTO lazada_products
(item_id, name, created_time, updated_time, primary_category, status, created_date)
SELECT
    6056230414 + n,  -- Changed base item_id to avoid conflicts
    'Túi Pickleball ' ||
    CASE (n % 10)
        WHEN 0 THEN 'Joola Vision II Backpack (Blue) '
        WHEN 1 THEN 'Wilson Pro Staff Bag (Black) '
        WHEN 2 THEN 'Adidas Sports Pack (Red) '
        WHEN 3 THEN 'Nike Athlete Duffel (Green) '
        WHEN 4 THEN 'Puma Performance Backpack (Orange) '
        WHEN 5 THEN 'Head Elite Duffle (Yellow) '
        WHEN 6 THEN 'Yonex Pro Series (Purple) '
        WHEN 7 THEN 'Babolat Team Line (White) '
        WHEN 8 THEN 'Prince Tour Pro (Gray) '
        WHEN 9 THEN 'Dunlop CX Series (Navy) '
    END || n,
    to_timestamp('1742835004738'::bigint/1000),
    to_timestamp('1742835004927'::bigint/1000),
    13156,
    'Active',
    CURRENT_DATE
FROM numbers;

-- Rest of the code remains the same, just update the item_id base number
WITH RECURSIVE numbers AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 1001
)
INSERT INTO lazada_skus
(item_id, sku_id, seller_sku, shop_sku, status, quantity, available, price, special_price, created_date)
SELECT
    6056230414 + n,  -- Changed to match new item_id
    44701183682 + n, -- Changed base sku_id
    '1234SKU_' || n,
    (6056230414 + n) || '_VNAMZ-' || (44701183682 + n),
    'active',
    100,
    100,
    250000,
    0,
    CURRENT_DATE
FROM numbers;

-- Then insert images
WITH RECURSIVE numbers AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 1001
)
INSERT INTO lazada_images
(item_id, image_url, created_date)
SELECT
    6056230414 + n,  -- Changed to match new item_id
    'https://picsum.photos/800/600?random=' || n,
    CURRENT_DATE
FROM numbers
UNION ALL
SELECT
    6056230414 + n,  -- Changed to match new item_id
    'https://picsum.photos/400/300?random=' || (n + 1000),
    CURRENT_DATE
FROM numbers;

-- Finally insert attributes with 10 different brands
WITH RECURSIVE numbers AS (
    SELECT 1 as n
    UNION ALL
    SELECT n + 1 FROM numbers WHERE n < 1001
)
INSERT INTO lazada_attributes
(item_id, brand, description, created_date)
SELECT
    6056230414 + n,  -- Changed to match new item_id
    CASE (n % 10)
        WHEN 0 THEN 'JOOLA'
        WHEN 1 THEN 'WILSON'
        WHEN 2 THEN 'ADIDAS'
        WHEN 3 THEN 'NIKE'
        WHEN 4 THEN 'PUMA'
        WHEN 5 THEN 'HEAD'
        WHEN 6 THEN 'YONEX'
        WHEN 7 THEN 'BABOLAT'
        WHEN 8 THEN 'PRINCE'
        WHEN 9 THEN 'DUNLOP'
    END,
    CASE
        WHEN n % 3 = 0 THEN 'Ba lô thể thao thiết kế hiện đại với nhiều ngăn tiện dụng. Chất liệu cao cấp, chống thấm nước tốt. Phù hợp cho các hoạt động thể thao và du lịch. Model ' || n
        WHEN n % 3 = 1 THEN 'Túi đựng vợt thể thao, thiết kế đặc biệt với ngăn đệm bảo vệ. Dây đeo vai có thể điều chỉnh, thoải mái khi sử dụng. Phiên bản giới hạn số ' || n
        ELSE 'Balo thể thao cao cấp. Thiết kế thông minh với ngăn chứa đồ riêng biệt. Chống sốc tốt, bảo vệ trang thiết bị. Phiên bản đặc biệt ' || n
    END,
    CURRENT_DATE
FROM numbers;

COMMIT;