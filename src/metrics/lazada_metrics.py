from prometheus_client import start_http_server, Gauge, Counter
from cassandra.cluster import Cluster
from cassandra.auth import PlainTextAuthProvider
from os import getenv
import time
import logging

# Metrics definition
PRICE_GAUGE = Gauge('lazada_product_price', 'Current product price', ['item_id', 'name'])
QUANTITY_GAUGE = Gauge('lazada_product_quantity', 'Current product quantity', ['item_id', 'name'])
PRICE_CHANGE_COUNTER = Counter('lazada_price_changes', 'Number of price changes', ['item_id'])
SMA_GAUGE = Gauge('lazada_price_sma', 'Simple Moving Average', ['item_id', 'period'])
EMA_GAUGE = Gauge('lazada_price_ema', 'Exponential Moving Average', ['item_id', 'period'])
RSI_GAUGE = Gauge('lazada_price_rsi', 'Relative Strength Index', ['item_id'])

class LazadaMetricsExporter:
    def __init__(self):
        self.cluster = Cluster([getenv('CASSANDRA_HOST', 'localhost')],
                             auth_provider=PlainTextAuthProvider(
                                 username=getenv('CASSANDRA_USER'),
                                 password=getenv('CASSANDRA_PASSWORD')))
        self.session = self.cluster.connect('lazada')

    def collect_metrics(self):
        while True:
            try:
                # Fetch latest product data
                rows = self.session.execute("""
                    SELECT item_id, name, price, quantity, 
                           sma_7, ema_14, rsi_14
                    FROM price_indicators
                    WHERE timestamp > NOW() - INTERVAL '1 hour'
                """)

                for row in rows:
                    # Update basic metrics
                    PRICE_GAUGE.labels(
                        item_id=str(row.item_id),
                        name=row.name
                    ).set(row.price)

                    QUANTITY_GAUGE.labels(
                        item_id=str(row.item_id),
                        name=row.name
                    ).set(row.quantity)

                    # Update technical indicators
                    SMA_GAUGE.labels(
                        item_id=str(row.item_id),
                        period='7d'
                    ).set(row.sma_7)

                    EMA_GAUGE.labels(
                        item_id=str(row.item_id),
                        period='14d'
                    ).set(row.ema_14)

                    RSI_GAUGE.labels(
                        item_id=str(row.item_id)
                    ).set(row.rsi_14)

            except Exception as e:
                logging.error(f"Error collecting metrics: {e}")

            time.sleep(60)  # Collect metrics every minute

def main():
    # Start Prometheus HTTP server
    start_http_server(8000)
    
    # Start metrics collection
    exporter = LazadaMetricsExporter()
    exporter.collect_metrics()

if __name__ == "__main__":
    main()