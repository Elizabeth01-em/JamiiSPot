import os
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'jamii.settings')
django.setup()

from django.urls import get_resolver
from django.conf import settings

def print_urls(urlpatterns, prefix=''):
    for pattern in urlpatterns:
        if hasattr(pattern, 'url_patterns'):
            # This is an include() pattern
            print(f"{prefix}{pattern.pattern} -> INCLUDE")
            print_urls(pattern.url_patterns, prefix + "  ")
        else:
            # This is a regular URL pattern
            print(f"{prefix}{pattern.pattern} -> {getattr(pattern, 'callback', 'Unknown')}")

print("Django URL Patterns:")
print("=" * 50)
resolver = get_resolver()
print_urls(resolver.url_patterns)
