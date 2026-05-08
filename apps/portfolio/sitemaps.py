from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Project

class StaticViewSitemap(Sitemap):
    priority = 0.5
    changefreq = 'monthly'
    
    def items(self):
        return ['portfolio:home', 'portfolio:about', 'portfolio:projects',
                'portfolio:skills', 'portfolio:experience', 'contact:contact']
    
    def location(self, item):
        return reverse(item)

class ProjectSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    
    def items(self):
        return Project.objects.filter(is_published=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        return obj.get_absolute_url()
