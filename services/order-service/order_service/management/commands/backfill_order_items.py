from django.core.management.base import BaseCommand
from orders.models import OrderItem
import requests
from django.conf import settings

class Command(BaseCommand):
    help = 'Backfill product_name and price for order items by calling catalog-service'

    def handle(self, *args, **options):
        # Find unique product IDs
        product_ids = set(OrderItem.objects.values_list('product_id', flat=True))

        if not product_ids:
            self.stdout.write("No products to backfill.")
            return

        self.stdout.write(f"Found {len(product_ids)} unique product_ids. Fetching data...")

        catalog_service_url = getattr(settings, 'CATALOG_SERVICE_INTERNAL_URL', 'http://localhost:8002/internal/products/bulk-lookup/')
        
        try:
            resp = requests.post(catalog_service_url, json={"ids": list(product_ids)})
            if resp.status_code == 200:
                products = resp.json()
                for prod in products:
                    pid = prod['ProductID']
                    name = prod.get('ProductName', '')
                    price = prod.get('UnitPrice', 0)
                    
                    OrderItem.objects.filter(product_id=pid).update(product_name=name, price=price)
                
                self.stdout.write(self.style.SUCCESS('Successfully backfilled product data on order items.'))
            else:
                self.stdout.write(self.style.ERROR(f'Failed to fetch products. Status {resp.status_code}'))
        except requests.RequestException as e:
            self.stdout.write(self.style.ERROR(f'Error connecting to catalog service: {str(e)}'))
