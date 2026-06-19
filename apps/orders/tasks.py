from celery import shared_task
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3)
def send_order_confirmation_email(self, order_id):
    """
    Send order confirmation email.
    Includes retry logic for failed attempts.
    """
    from .models import Order
    
    try:
        order = Order.objects.select_related('store').get(id=order_id)
        
        # Log the email sending (simulating actual email send)
        logger.info(f" Sending order confirmation for Order #{order.id}")
        logger.info(f" Store: {order.store.name}")
        logger.info(f" Status: {order.status}")
        logger.info(f" Total Items: {order.get_total_items()}")
        logger.info(f" Order Total: ${order.get_order_items_cost()}")
        
        # In production, you would send actual email here:
        # subject = f"Order #{order.id} Confirmation"
        # message = render_to_string('orders/confirmation_email.html', {'order': order})
        # send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, [customer_email])
        
        logger.info(f"Order confirmation email queued successfully for Order #{order.id}")
        
        return f"Order confirmation email sent for order {order_id}"
        
    except Order.DoesNotExist:
        logger.error(f"Order {order_id} not found")
        return f"Order {order_id} not found"
    
    except Exception as exc:
        logger.error(f"Error sending order confirmation: {str(exc)}")
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=60 * (2 ** self.request.retries))
