WITH product_metrics AS (
    SELECT 
        a.brand,
        p.primary_category,
        COUNT(DISTINCT p.item_id) as total_products,
        SUM(s.quantity * s.price) as total_revenue,
        SUM(s.quantity * COALESCE(s.special_price, s.price)) as actual_revenue,
        SUM(s.quantity) as total_units_sold,
        SUM(CASE WHEN s.quantity <= 10 THEN 1 ELSE 0 END) as low_stock_count,
        COUNT(DISTINCT CASE WHEN s.special_price > 0 THEN p.item_id END) as discounted_items
    FROM lazada_products p
    JOIN lazada_skus s ON p.item_id = s.item_id
    JOIN lazada_attributes a ON p.item_id = a.item_id
    GROUP BY a.brand, p.primary_category
),
roi_analysis AS (
    SELECT 
        brand,
        primary_category,
        total_revenue,
        actual_revenue,
        (total_revenue - actual_revenue) as discount_impact,
        ROUND(((actual_revenue - total_revenue) / NULLIF(total_revenue, 0) * 100)::numeric, 2) as roi_percentage,
        ROUND((total_units_sold::decimal / NULLIF(total_products, 0)), 2) as units_per_product,
        ROUND((low_stock_count::decimal / NULLIF(total_products, 0) * 100), 2) as low_stock_percentage,
        ROUND((discounted_items::decimal / NULLIF(total_products, 0) * 100), 2) as discount_percentage
    FROM product_metrics
)
SELECT 
    'Revenue Impact' as impact_category,
    'Actual Revenue' as metric_name,
    actual_revenue as value,
    ROUND((actual_revenue / NULLIF(total_revenue, 0) * 100), 2) as percentage
FROM roi_analysis
UNION ALL
SELECT 
    'Revenue Impact',
    'Discount Loss',
    discount_impact,
    ROUND((discount_impact / NULLIF(total_revenue, 0) * 100), 2)
FROM roi_analysis
UNION ALL
SELECT 
    'Inventory Health',
    'Low Stock Products',
    low_stock_count,
    low_stock_percentage
FROM product_metrics
UNION ALL
SELECT 
    'Pricing Strategy',
    'Discounted Products',
    discounted_items,
    discount_percentage
FROM product_metrics
UNION ALL
SELECT 
    'Sales Efficiency',
    'Sales per Product',
    total_units_sold,
    ROUND((total_units_sold::decimal / NULLIF(total_products, 0) * 100), 2)
FROM product_metrics
ORDER BY impact_category, percentage DESC;WITH price_changes AS (
    SELECT 
        p.item_id,
        p.name,
        s.sku_id,
        s.price,
        s.special_price,
        CASE 
            WHEN s.price <= 100000 THEN '0-100k'
            WHEN s.price <= 200000 THEN '100k-200k'
            WHEN s.price <= 500000 THEN '200k-500k'
            WHEN s.price <= 1000000 THEN '500k-1M'
            ELSE 'Over 1M'
        END as price_range,
        CASE
            WHEN s.special_price > 0 THEN 
                ROUND(((s.price - s.special_price) / s.price * 100)::numeric, 2)
            ELSE 0
        END as discount_percentage,
        CASE
            WHEN s.special_price > 0 THEN true
            ELSE false
        END as is_discounted,
        s.quantity,
        s.available
    FROM lazada_products p
    JOIN lazada_skus s ON p.item_id = s.item_id
),
inventory_distribution AS (
    SELECT 
        CASE 
            WHEN quantity <= 10 THEN '0-10'
            WHEN quantity <= 25 THEN '11-25'
            WHEN quantity <= 50 THEN '26-50'
            WHEN quantity <= 100 THEN '51-100'
            ELSE 'Over 100'
        END as stock_range,
        COUNT(*) as product_count,
        AVG(price) as avg_price,
        SUM(quantity) as total_stock
    FROM price_changes
    GROUP BY 
        CASE 
            WHEN quantity <= 10 THEN '0-10'
            WHEN quantity <= 25 THEN '11-25'
            WHEN quantity <= 50 THEN '26-50'
            WHEN quantity <= 100 THEN '51-100'
            ELSE 'Over 100'
        END
),
discount_distribution AS (
    SELECT 
        CASE 
            WHEN discount_percentage = 0 THEN 'No Discount'
            WHEN discount_percentage <= 10 THEN '1-10%'
            WHEN discount_percentage <= 25 THEN '11-25%'
            WHEN discount_percentage <= 50 THEN '26-50%'
            ELSE 'Over 50%'
        END as discount_range,
        COUNT(*) as product_count,
        AVG(price) as avg_original_price,
        AVG(special_price) as avg_special_price
    FROM price_changes
    GROUP BY 
        CASE 
            WHEN discount_percentage = 0 THEN 'No Discount'
            WHEN discount_percentage <= 10 THEN '1-10%'
            WHEN discount_percentage <= 25 THEN '11-25%'
            WHEN discount_percentage <= 50 THEN '26-50%'
            ELSE 'Over 50%'
        END
)
SELECT 
    'Price Distribution' as metric_type,
    price_range as range_bucket,
    COUNT(*) as count,
    ROUND(AVG(price)::numeric, 2) as avg_value,
    SUM(quantity) as total_quantity
FROM price_changes
GROUP BY price_range
UNION ALL
SELECT 
    'Stock Distribution' as metric_type,
    stock_range as range_bucket,
    product_count as count,
    ROUND(avg_price::numeric, 2) as avg_value,
    total_stock as total_quantity
FROM inventory_distribution
UNION ALL
SELECT 
    'Discount Distribution' as metric_type,
    discount_range as range_bucket,
    product_count as count,
    ROUND(avg_original_price::numeric, 2) as avg_value,
    0 as total_quantity
FROM discount_distribution
ORDER BY metric_type, range_bucket;