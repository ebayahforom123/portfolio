from django.apps import AppConfig


class BlogConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.blog'
    verbose_name = 'Blog'

    def ready(self):
        """Import signals when app is ready"""
        try:
            import apps.blog.signals
        except ImportError:
            pass