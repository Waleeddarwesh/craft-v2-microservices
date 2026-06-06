import os
import re

services = {
    'auth-service': ('8001', 'auth_service.wsgi:application'),
    'catalog-service': ('8002', 'catalog_service.wsgi:application'),
    'order-service': ('8003', 'order_service.wsgi:application'),
    'payment-service': ('8004', 'payment_service.wsgi:application'),
    'platform-service': ('8005', 'platform_service.wsgi:application'),
    'reporting-service': ('8007', 'reporting_service.wsgi:application'),
}

for s, (port, wsgi) in services.items():
    df_path = os.path.join('services', s, 'Dockerfile')
    if not os.path.exists(df_path): continue
    with open(df_path, 'r') as f:
        content = f.read()
    
    # Add collectstatic before CMD if not present
    if 'collectstatic' not in content:
        content = re.sub(r'(CMD \[)', r'RUN python manage.py collectstatic --noinput\n\n\1', content)
        
    # Replace CMD
    new_cmd = f'CMD ["gunicorn", "{wsgi}", "--bind", "0.0.0.0:{port}", "--workers", "3"]'
    content = re.sub(r'CMD \[.*?\]', new_cmd, content)
    
    with open(df_path, 'w') as f:
        f.write(content)
    print(f'Updated {df_path}')

# Fix realtime-service
rt_path = os.path.join('services', 'realtime-service', 'Dockerfile')
if os.path.exists(rt_path):
    with open(rt_path, 'r') as f:
        rt_content = f.read()
    rt_content = re.sub(r'\"8005\"', r'\"8008\"', rt_content)
    with open(rt_path, 'w') as f:
        f.write(rt_content)
    print(f'Updated {rt_path}')
