from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.cache import cache
from .models import ContactMessage, FAQ


@receiver(post_save, sender=ContactMessage)
def clear_contact_cache(sender, instance, **kwargs):
    """Clear cache when new contact message is created"""
    cache.delete('contact_stats')
    cache.delete('unread_messages_count')


@receiver(post_save, sender=FAQ)
def clear_faq_cache(sender, instance, **kwargs):
    """Clear FAQ cache when FAQ is updated"""
    cache.delete('faq_data')