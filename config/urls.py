from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.views.generic import RedirectView, TemplateView

urlpatterns = [
    # Admin
    path('admin/', admin.site.urls),
    
    # Portfolio app (main app)
    path('', include('apps.portfolio.urls', namespace='portfolio')),
    
    # Blog app
    path('blog/', include('apps.blog.urls', namespace='blog')),
    
    # Contact app
    path('contact/', include('apps.contact.urls', namespace='contact')),
    
    # Robots.txt
    path('robots.txt', TemplateView.as_view(
        template_name='robots.txt',
        content_type='text/plain'
    ), name='robots_txt'),
    
    # Sitemap
    path('sitemap.xml', TemplateView.as_view(
        template_name='sitemap.xml',
        content_type='application/xml'
    ), name='sitemap'),
    
    # Favicon
    path('favicon.ico', RedirectView.as_view(
        url='/static/images/favicon.ico',
        permanent=True
    )),
]

# Development-only URLs
if settings.DEBUG:
    # Try to add debug toolbar, but don't crash if not available
    try:
        import debug_toolbar
        urlpatterns += [
            path('__debug__/', include('debug_toolbar.urls')),
        ]
    except (ImportError, RuntimeError):
        pass
    
    # Serve media and static files
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
