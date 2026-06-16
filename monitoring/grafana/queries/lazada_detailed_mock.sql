WITH RECURSIVE generate_dates AS (
    SELECT NOW() - INTERVAL '30 days' as date_stamp
    UNION ALL
    SELECT date_stamp + INTERVAL '1 day'
    FROM generate_dates
    WHERE date_stamp < NOW()
),
generate_brands AS (
    SELECT unnest(ARRAY[
        'JOOLA', 'STIGA', 'BUTTERFLY', 'DONIC', 
        'YASAKA', 'DHS', 'TIBHAR', 'XIOM',
        'NITTAKU', 'TSP', 'ANDRO', '729'
    ]) as brand
),
mock_metrics AS (
    SELECT 
        d.date_stamp,
        b.brand,
        -- Product Metrics
        (100 + (random() * 500))::int as total_products,
        (50 + (random() * 200))::int as active_listings,
        (10 + (random() * 40))::int as new_listings,
        (5 + (random() * 15))::int as removed_listings,
        
        -- Inventory Metrics
        (1000 + (random() * 5000))::int as total_stock,
        (10 + (random() * 50))::int as low_stock_items,
        (5 + (random() * 20))::int as out_of_stock,
        (20 + (random() * 100))::int as excess_stock,
        
        -- Sales Metrics
        (50 + (random() * 300))::int as units_sold,
        (5 + (random() * 30))::int as orders_count,
        (2 + (random() * 8))::numeric as avg_order_size,
        
        -- Revenue Metrics
        (5000000 + (random() * 20000000))::numeric as gross_revenue,
        (4000000 + (random() * 15000000))::numeric as net_revenue,
        (500000 + (random() * 2000000))::numeric as discount_amount,
        
        -- Price Metrics
        (200000 + (random() * 1000000))::numeric as avg_price,
        (150000 + (random() * 800000))::numeric as median_price,
        (100000 + (random() * 500000))::numeric as min_price,
        (1000000 + (random() * 5000000))::numeric as max_price,
        
        -- Performance Metrics
        (random() * 100)::numeric as conversion_rate,
        (random() * 50)::numeric as return_rate,
        (70 + (random() * 30))::numeric as fulfillment_rate,
        (random() * 20)::numeric as cancellation_rate,
        
        -- Marketing Metrics
        (20 + (random() * 100))::int as promo_products,
        (10 + (random() * 40))::numeric as avg_discount_percent,
        (1000 + (random() * 5000))::int as page_views,
        (100 + (random() * 1000))::int as unique_visitors
    FROM generate_dates d
    CROSS JOIN generate_brands b
)
SELECT 
    date_stamp as "Date",
    brand as "Brand",
    
    -- Product Portfolio
    total_products as "Total Products",
    active_listings as "Active Listings",
    new_listings as "New Listings",
    removed_listings as "Removed Listings",
    ROUND((active_listings::decimal / NULLIF(total_products, 0) * 100), 2) as "Active Products %",
    
    -- Inventory Health
    total_stock as "Total Stock",
    low_stock_items as "Low Stock Items",
    out_of_stock as "Out of Stock",
    excess_stock as "Excess Stock",
    ROUND((low_stock_items + out_of_stock)::decimal / NULLIF(total_products, 0) * 100, 2) as "Stock Risk %",
    
    -- Sales Performance
    units_sold as "Units Sold",
    orders_count as "Order Count",
    ROUND(avg_order_size::numeric, 2) as "Avg Order Size",
    ROUND((units_sold::decimal / NULLIF(total_stock, 0) * 100), 2) as "Stock Turnover %",
    
    -- Financial Metrics
    ROUND(gross_revenue::numeric, 2) as "Gross Revenue",
    ROUND(net_revenue::numeric, 2) as "Net Revenue",
    ROUND(discount_amount::numeric, 2) as "Total Discounts",
    ROUND((discount_amount / NULLIF(gross_revenue, 0) * 100), 2) as "Discount %",
    
    -- Price Analysis
    ROUND(avg_price::numeric, 2) as "Average Price",
    ROUND(median_price::numeric, 2) as "Median Price",
    ROUND(min_price::numeric, 2) as "Min Price",
    ROUND(max_price::numeric, 2) as "Max Price",
    
    -- Performance Indicators
    ROUND(conversion_rate::numeric, 2) as "Conversion Rate %",
    ROUND(return_rate::numeric, 2) as "Return Rate %",
    ROUND(fulfillment_rate::numeric, 2) as "Fulfillment Rate %",
    ROUND(cancellation_rate::numeric, 2) as "Cancellation Rate %",
    
    -- Marketing Effectiveness
    promo_products as "Products on Promotion",
    ROUND(avg_discount_percent::numeric, 2) as "Avg Discount %",
    page_views as "Page Views",
    unique_visitors as "Unique Visitors",
    ROUND((unique_visitors::decimal / NULLIF(page_views, 0) * 100), 2) as "Visitor Engagement %"
    
FROM mock_metrics
ORDER BY date_stamp DESC, net_revenue DESC;