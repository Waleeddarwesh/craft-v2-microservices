import os
import glob
import re

services = ['auth-service', 'catalog-service', 'order-service', 'payment-service', 'platform-service', 'reporting-service']

for s in services:
    settings_files = glob.glob(os.path.join('services', s, '*', 'settings.py'))
    if not settings_files: continue
    s_path = settings_files[0]
    
    with open(s_path, 'r') as f:
        content = f.read()
    
    # ALLOWED_HOSTS
    content = re.sub(
        r"ALLOWED_HOSTS\s*=\s*\[.*?\]",
        "ALLOWED_HOSTS = env.list('ALLOWED_HOSTS', default=['*'])",
        content
    )
    
    # MIDDLEWARE
    if 'WhiteNoiseMiddleware' not in content:
        content = re.sub(
            r"('django\.middleware\.security\.SecurityMiddleware',)",
            r"\1\n    'whitenoise.middleware.WhiteNoiseMiddleware',",
            content
        )
        
    # STATIC_ROOT
    if 'STATIC_ROOT' not in content:
        content = re.sub(
            r"(STATIC_URL\s*=\s*['\"]static/['\"])",
            r"\1\nSTATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')",
            content
        )
    
    with open(s_path, 'w') as f:
        f.write(content)
    
    print(f'Updated {s_path}')
