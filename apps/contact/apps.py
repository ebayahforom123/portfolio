from django.apps import AppConfig


class ContactConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.contact'
    verbose_name = 'Contact Messages'

    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.contact.signals
        except ImportError:
            pass