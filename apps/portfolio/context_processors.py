from .models import SiteSettings

def site_settings(request):
    """Add site settings to all templates"""
    try:
        settings = SiteSettings.objects.first()
        if settings:
            return {'site_settings': settings}
    except:
        pass
    
    # Fallback
    return {
        'site_settings': {
            'site_name': 'My Portfolio',
            'site_description': 'Professional Portfolio',
            'tagline': 'Full Stack Developer',
            'short_bio': 'Building amazing web applications.',
            'about_me': '<p>Content coming soon.</p>',
            'email': '',
            'phone': '',
            'location': '',
            'availability': '',
        }
    }
