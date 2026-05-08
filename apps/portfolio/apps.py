from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.portfolio'
    verbose_name = 'Portfolio'

    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.portfolio.signals
        except ImportError:
            pass