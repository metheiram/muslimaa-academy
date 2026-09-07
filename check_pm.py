import os
os.environ['DJANGO_SETTINGS_MODULE'] = 'config.settings'
import django
django.setup()
from payments.models import PaymentMethod
for pm in PaymentMethod.objects.filter(is_active=True):
    print(f"Method: {pm.get_method_display()}")
    print(f"Number: {pm.account_number}")
    print(f"Title: {pm.account_title}")
    print(f"Instructions: {pm.instructions}")
    print("---")
