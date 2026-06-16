-- Product Analytics by Category
WITH price_stats AS (
    SELECT 
        p.primary_category,
        COUNT(DISTINCT p.item_id) as total_products,
        COUNT(DISTINCT s.sku_id) as total_skus,
        AVG(s.price) as avg_price,
        MAX(s.price) as max_price,
        MIN(s.price) as min_price,
        SUM(s.quantity) as total_inventory,
        SUM(s.quantity * s.price) as inventory_value
    FROM lazada_products p
    JOIN lazada_skus s ON p.item_id = s.item_id
    GROUP BY p.primary_category
),
inventory_metrics AS (
    SELECT 
        p.primary_category,
        COUNT(CASE WHEN s.quantity > 50 THEN 1 END) as high_stock_items,
        COUNT(CASE WHEN s.quantity <= 20 THEN 1 END) as low_stock_items,
        AVG(s.quantity) as avg_stock_level,
        SUM(CASE WHEN s.special_price > 0 THEN 1 ELSE 0 END) as items_on_sale
    FROM lazada_products p
    JOIN lazada_skus s ON p.item_id = s.item_id
    GROUP BY p.primary_category
),
image_metrics AS (
    SELECT 
        p.primary_category,
        COUNT(i.image_url) as total_images,
        COUNT(DISTINCT i.item_id) as products_with_images,
        ROUND(COUNT(i.image_url)::DECIMAL / COUNT(DISTINCT i.item_id), 2) as avg_images_per_product
    FROM lazada_products p
    LEFT JOIN lazada_images i ON p.item_id = i.item_id
    GROUP BY p.primary_category
),
brand_metrics AS (
    SELECT 
        p.primary_category,
        COUNT(DISTINCT a.brand) as unique_brands,
        MODE() WITHIN GROUP (ORDER BY a.brand) as most_common_brand,
        COUNT(CASE WHEN LENGTH(a.description) > 500 THEN 1 END) as detailed_descriptions
    FROM lazada_products p
    LEFT JOIN lazada_attributes a ON p.item_id = a.item_id
    GROUP BY p.primary_category
)
SELECT 
    ps.primary_category,
    ps.total_products as "Total Products",
    ps.total_skus as "Total SKUs",
    ROUND(ps.avg_price::numeric, 2) as "Average Price",
    ps.max_price as "Highest Price",
    ps.min_price as "Lowest Price",
    ps.total_inventory as "Total Inventory",
    ROUND(ps.inventory_value::numeric, 2) as "Inventory Value",
    im.high_stock_items as "High Stock Items",
    im.low_stock_items as "Low Stock Items",
    ROUND(im.avg_stock_level::numeric, 2) as "Average Stock Level",
    im.items_on_sale as "Items on Sale",
    img.total_images as "Total Images",
    img.products_with_images as "Products with Images",
    img.avg_images_per_product as "Avg Images per Product",
    bm.unique_brands as "Unique Brands",
    bm.most_common_brand as "Most Common Brand",
    bm.detailed_descriptions as "Detailed Descriptions",
    ROUND((im.items_on_sale::decimal / ps.total_products * 100), 2) as "Sale Items Percentage",
    ROUND((ps.inventory_value / NULLIF(ps.total_inventory, 0))::numeric, 2) as "Average Item Value"
FROM price_stats ps
JOIN inventory_metrics im ON ps.primary_category = im.primary_category
JOIN image_metrics img ON ps.primary_category = img.primary_category
JOIN brand_metrics bm ON ps.primary_category = bm.primary_category
WHERE ps.total_products > 0
ORDER BY ps.inventory_value DESC;