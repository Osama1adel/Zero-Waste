from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from apps.core.models import RestaurantCompany, Branch
from apps.inventory.models import Product, StockItem
from apps.notifications.models import UserNotification
from django.utils import timezone
import random
import datetime

User = get_user_model()

class Command(BaseCommand):
    help = 'Seeds the database with initial test data'

    def handle(self, *args, **options):
        self.stdout.write('Seeding data...')

        # 1. Create Superuser
        if not User.objects.filter(username='admin').exists():
            User.objects.create_superuser('admin', 'admin@example.com', 'admin123')
            self.stdout.write(self.style.SUCCESS('Superuser created: admin/admin123'))

        # 2. Create Company
        company, _ = RestaurantCompany.objects.get_or_create(
            name='Tuwaiq Foods',
            defaults={
                'subscription_status': True
            }
        )

        # 3. Create Branch
        branch, _ = Branch.objects.get_or_create(
            name='Riyadh Main Branch',
            company=company,
            defaults={
                'location': 'Riyadh'
            }
        )

        # 4. Create Branch Manager
        manager_username = 'manager1'
        if not User.objects.filter(username=manager_username).exists():
            manager = User.objects.create_user(
                username=manager_username,
                email='manager@tuwaiq.com',
                password='password123',
                role='branch_manager'
            )
            branch.manager = manager
            branch.save()
            self.stdout.write(self.style.SUCCESS(f'Branch Manager created: {manager_username}/password123'))
        else:
            manager = User.objects.get(username=manager_username)
            if not branch.manager:
                branch.manager = manager
                branch.save()
                self.stdout.write(self.style.SUCCESS(f'Fixed Branch for existing user: {manager_username}'))

        # 5. Create Products & Stock
        products = ['Burger Bun', 'Beef Patty', 'Cheese Slice', 'Lettuce', 'Tomato']
        for p_name in products:
            product, _ = Product.objects.get_or_create(
                name=p_name,
                company=company,
                defaults={
                    'minimum_quantity': 10, 
                    'unit': 'kg',
                    'sku': f'SKU-{random.randint(1000, 9999)}'
                }
            )
            StockItem.objects.get_or_create(
                branch=branch,
                product=product,
                defaults={
                    'quantity': random.randint(5, 50),
                    'expiry_date': timezone.now().date() + datetime.timedelta(days=30),
                    'batch_id': f'BATCH-{random.randint(100, 999)}'
                }
            )

        # 6. Create Notifications
        titles = ['Welcome to Zero Waste', 'Low Stock Alert', 'New System Update']
        for title in titles:
            UserNotification.objects.create(
                user=manager,
                title=title,
                message=f'This is a test notification for {title}',
                notification_type='system_update' if 'Update' in title else 'alert',
                is_read=False
            )

        self.stdout.write(self.style.SUCCESS('Data seeded successfully!'))
