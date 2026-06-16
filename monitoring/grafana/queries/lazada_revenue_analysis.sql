WITH daily_revenue AS (
    SELECT 
        DATE_TRUNC('day', p.created_time) as sale_date,
        a.brand,
        COUNT(DISTINCT p.item_id) as products_sold,
        SUM(s.quantity) as units_sold,
        SUM(s.quantity * s.price) as gross_revenue,
        SUM(CASE 
            WHEN s.special_price > 0 THEN s.quantity * (s.price - s.special_price)
            ELSE 0 
        END) as discount_value,
        COUNT(DISTINCT CASE WHEN s.special_price > 0 THEN p.item_id END) as discounted_products
    FROM lazada_products p
    JOIN lazada_skus s ON p.item_id = s.item_id
    JOIN lazada_attributes a ON p.item_id = a.item_id
    WHERE p.created_time >= NOW() - INTERVAL '30 days'
    GROUP BY DATE_TRUNC('day', p.created_time), a.brand
),
performance_metrics AS (
    SELECT 
        sale_date,
        brand,
        products_sold,
        units_sold,
        gross_revenue,
        discount_value,
        (gross_revenue - discount_value) as net_revenue,
        ROUND((discount_value / NULLIF(gross_revenue, 0) * 100), 2) as discount_percentage,
        ROUND((units_sold::decimal / NULLIF(products_sold, 0)), 2) as units_per_product,
        LAG(gross_revenue) OVER (PARTITION BY brand ORDER BY sale_date) as prev_day_revenue,
        LAG(units_sold) OVER (PARTITION BY brand ORDER BY sale_date) as prev_day_units
    FROM daily_revenue
)
SELECT 
    sale_date,
    brand,
    products_sold as "Products Sold",
    units_sold as "Units Sold",
    ROUND(gross_revenue::numeric, 2) as "Gross Revenue",
    ROUND(net_revenue::numeric, 2) as "Net Revenue",
    ROUND(discount_value::numeric, 2) as "Total Discounts",
    discount_percentage as "Discount %",
    units_per_product as "Units per Product",
    CASE 
        WHEN prev_day_revenue IS NOT NULL THEN 
            ROUND(((gross_revenue - prev_day_revenue) / NULLIF(prev_day_revenue, 0) * 100)::numeric, 2)
        ELSE 0
    END as "Revenue Growth %",
    CASE 
        WHEN prev_day_units IS NOT NULL THEN 
            ROUND(((units_sold - prev_day_units) / NULLIF(prev_day_units, 0) * 100)::numeric, 2)
        ELSE 0
    END as "Sales Growth %",
    ROUND((net_revenue / NULLIF(units_sold, 0))::numeric, 2) as "Average Order Value"
FROM performance_metrics
ORDER BY sale_date DESC, net_revenue DESC;