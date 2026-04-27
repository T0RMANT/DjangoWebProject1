import datetime

from django.core.management.base import BaseCommand
from django.utils import timezone

from app.models import Order


class Command(BaseCommand):
    help = 'Cancels unpaid orders that are older than 12 hours.'

    def handle(self, *args, **options):
        self.stdout.write(self.style.NOTICE('Starting to cancel old, unpaid orders...'))

        # Calculate the time 12 hours ago from now
        time_threshold = timezone.now() - datetime.timedelta(hours=12)

        # Find orders that are unpaid, not already cancelled, and older than the threshold
        orders_to_cancel = Order.objects.filter(
            created__lt=time_threshold,
            paid=False,
            status='processing'  # We only want to cancel orders that are still in processing
        )

        cancelled_count = 0
        for order in orders_to_cancel:
            order.status = 'cancelled'
            order.save()
            cancelled_count += 1

        if cancelled_count > 0:
            self.stdout.write(self.style.SUCCESS(f'Successfully cancelled {cancelled_count} orders.'))
        else:
            self.stdout.write(self.style.SUCCESS('No old, unpaid orders to cancel.'))

