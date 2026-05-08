from django import template
from django.utils.safestring import mark_safe
from django.utils import timezone
from django.db.models import Count, Q
from ..models import Project, Skill, Technology, Testimonial, Experience

register = template.Library()


@register.simple_tag
def get_featured_projects(count=3):
    """Get featured projects"""
    return (
        Project.objects
        .filter(is_published=True, is_featured=True)
        .prefetch_related('technologies')
        .order_by('-order', '-created_at')[:count]
    )


@register.simple_tag
def get_recent_projects(count=6):
    """Get recent projects"""
    return (
        Project.objects
        .filter(is_published=True)
        .prefetch_related('technologies')
        .order_by('-created_at')[:count]
    )


@register.simple_tag
def get_skill_categories():
    """Get all skill categories with skills"""
    return (
        Skill.objects
        .select_related('category')
        .filter(category__isnull=False)
        .order_by('category__order', 'order')
    )


@register.simple_tag
def get_latest_testimonials(count=5):
    """Get latest testimonials"""
    return (
        Testimonial.objects
        .filter(is_active=True)
        .order_by('-created_at')[:count]
    )


@register.filter
def multiply(value, arg):
    """Multiply filter"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''


@register.filter
def percentage(value, total):
    """Calculate percentage"""
    try:
        return (float(value) / float(total)) * 100
    except (ValueError, ZeroDivisionError, TypeError):
        return 0


@register.filter
def duration_years(start_date, end_date=None):
    """Calculate years between two dates"""
    if not start_date:
        return 0
    
    end = end_date or timezone.now().date()
    days = (end - start_date).days
    return round(days / 365, 1)


@register.filter
def truncate_chars(value, max_chars=100):
    """Truncate text after a certain number of characters"""
    if not value:
        return ''
    
    if len(value) <= max_chars:
        return value
    
    return value[:max_chars].rsplit(' ', 1)[0] + '...'


@register.inclusion_tag('includes/project_card.html')
def render_project_card(project):
    """Render a project card"""
    return {
        'project': project,
        'technologies': project.technologies.all(),
    }


@register.inclusion_tag('includes/social_links.html')
def render_social_links(site_settings):
    """Render social media links"""
    links = []
    social_platforms = [
        ('github', 'fab fa-github', 'GitHub'),
        ('linkedin', 'fab fa-linkedin', 'LinkedIn'),
        ('twitter', 'fab fa-twitter', 'Twitter'),
        ('stackoverflow', 'fab fa-stack-overflow', 'Stack Overflow'),
        ('medium', 'fab fa-medium', 'Medium'),
        ('youtube', 'fab fa-youtube', 'YouTube'),
        ('instagram', 'fab fa-instagram', 'Instagram'),
    ]
    
    for field, icon, name in social_platforms:
        url = getattr(site_settings, field, None)
        if url:
            links.append({
                'url': url,
                'icon': icon,
                'name': name,
                'field': field,
            })
    
    return {'links': links}


@register.inclusion_tag('includes/skill_bar.html')
def render_skill_bar(skill):
    """Render a skill progress bar"""
    return {
        'skill': skill,
        'proficiency_class': (
            'bg-success' if skill.proficiency >= 75
            else 'bg-warning' if skill.proficiency >= 50
            else 'bg-danger'
        ),
    }


@register.simple_tag
def get_project_stats():
    """Get project statistics"""
    projects = Project.objects.filter(is_published=True)
    
    return {
        'total': projects.count(),
        'featured': projects.filter(is_featured=True).count(),
        'by_type': [],
        'technologies': [],
    }


@register.filter
def star_rating(rating):
    """Convert rating to star HTML"""
    if not rating:
        return mark_safe('☆☆☆☆☆')
    
    stars = ''
    for i in range(5):
        if i < rating:
            stars += '<i class="fas fa-star text-warning"></i> '
        else:
            stars += '<i class="far fa-star text-warning"></i> '
    
    return mark_safe(stars.strip())
