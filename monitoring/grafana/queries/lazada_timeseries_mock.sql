WITH RECURSIVE generate_hours AS (
    SELECT 
        NOW() - INTERVAL '7 days' as hour_stamp
    UNION ALL
    SELECT 
        hour_stamp + INTERVAL '1 hour'
    FROM generate_hours
    WHERE hour_stamp < NOW()
),
generate_brands AS (
    SELECT unnest(ARRAY['JOOLA', 'STIGA', 'BUTTERFLY', 'DONIC']) as brand
),
mock_data AS (
    SELECT 
        h.hour_stamp as time_bucket,
        b.brand,
        -- Simulate daily patterns with sine wave and random variations
        (50 + (25 * sin((EXTRACT(HOUR FROM h.hour_stamp)::float / 24) * 2 * pi())) + 
            (random() * 20))::int as products_count,
        (200 + (100 * sin((EXTRACT(HOUR FROM h.hour_stamp)::float / 24) * 2 * pi())) + 
            (random() * 50))::int as total_units,
        (1000000 + (500000 * sin((EXTRACT(HOUR FROM h.hour_stamp)::float / 24) * 2 * pi())) + 
            (random() * 200000))::numeric as gross_revenue,
        (800000 + (400000 * sin((EXTRACT(HOUR FROM h.hour_stamp)::float / 24) * 2 * pi())) + 
            (random() * 150000))::numeric as actual_revenue,
        (20 + (10 * sin((EXTRACT(HOUR FROM h.hour_stamp)::float / 24) * 2 * pi())) + 
            (random() * 5))::int as items_on_sale,
        (250000 + (random() * 50000))::numeric as avg_price
    FROM generate_hours h
    CROSS JOIN generate_brands b
    WHERE h.hour_stamp <= NOW()
),
moving_averages AS (
    SELECT 
        time_bucket,
        brand,
        products_count,
        total_units,
        gross_revenue,
        actual_revenue,
        items_on_sale,
        avg_price,
        AVG(gross_revenue) OVER (
            PARTITION BY brand 
            ORDER BY time_bucket 
            ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
        ) as revenue_24h_ma,
        AVG(total_units) OVER (
            PARTITION BY brand 
            ORDER BY time_bucket 
            ROWS BETWEEN 23 PRECEDING AND CURRENT ROW
        ) as units_24h_ma
    FROM mock_data
)
SELECT 
    time_bucket,
    brand,
    products_count as "New Products",
    total_units as "Units Sold",
    ROUND(gross_revenue::numeric, 2) as "Gross Revenue",
    ROUND(actual_revenue::numeric, 2) as "Net Revenue",
    ROUND(((gross_revenue - actual_revenue) / NULLIF(gross_revenue, 0) * 100), 2) as "Discount Rate %",
    items_on_sale as "Products on Sale",
    ROUND(avg_price::numeric, 2) as "Average Price",
    ROUND(revenue_24h_ma::numeric, 2) as "24h Revenue MA",
    ROUND(units_24h_ma::numeric, 2) as "24h Units MA",
    ROUND(((actual_revenue - LAG(actual_revenue) OVER (PARTITION BY brand ORDER BY time_bucket)) 
        / NULLIF(LAG(actual_revenue) OVER (PARTITION BY brand ORDER BY time_bucket), 0) * 100), 2) as "Revenue Growth %"
FROM moving_averages
ORDER BY time_bucket DESC, brand;