from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from .models import (
    SiteSettings, SkillCategory, Skill, Technology,
    Project, ProjectImage, Experience, Education,
    Testimonial, Service, Resume
)


class BaseAdmin(admin.ModelAdmin):
    """Base admin with common configurations"""
    save_on_top = True


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    """Admin for singleton site settings"""
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'tagline', 'site_description', 'about_me', 'short_bio')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'location', 'availability')
        }),
        ('Social Links', {
            'fields': ('github', 'linkedin', 'twitter', 'stackoverflow', 'medium', 'youtube', 'instagram'),
            'classes': ('collapse',)
        }),
        ('Brand Assets', {
            'fields': ('profile_image', 'resume', 'favicon')
        }),
        ('SEO & Analytics', {
            'fields': ('google_analytics_id', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(SkillCategory)
class SkillCategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'order')
    list_editable = ('order',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Skill)
class SkillAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'proficiency', 'proficiency_bar', 'level', 'is_featured', 'order')
    list_filter = ('category', 'level', 'is_featured')
    list_editable = ('proficiency', 'level', 'is_featured', 'order')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}

    def proficiency_bar(self, obj):
        """Display proficiency as colored bar"""
        color = '#27ae60' if obj.proficiency >= 75 else '#f39c12' if obj.proficiency >= 50 else '#e74c3c'
        return format_html(
            '<div style="background:#eee; width:100px; height:20px; border-radius:10px; overflow:hidden;">'
            '<div style="background:{}; width:{}%; height:100%; transition: width 0.3s;"></div>'
            '</div>',
            color, obj.proficiency
        )

    proficiency_bar.short_description = 'Proficiency'


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order')
    list_filter = ('category', 'is_active')
    list_editable = ('category', 'is_active', 'order')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1
    fields = ('image', 'caption', 'is_featured', 'order')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'project_type', 'status', 'status_badge',
        'is_featured', 'is_published', 'created_at'
    )
    list_filter = ('status', 'project_type', 'is_featured', 'is_published')
    list_editable = ('is_featured', 'is_published', 'status')
    search_fields = ('title', 'short_description', 'description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('technologies', 'skills_demonstrated')
    inlines = [ProjectImageInline]
    date_hierarchy = 'created_at'

    def status_badge(self, obj):
        colors = {
            'draft': '#95a5a6',
            'in_progress': '#f39c12',
            'completed': '#27ae60',
            'maintenance': '#3498db',
            'archived': '#7f8c8d',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background:{}; color:white; padding:4px 12px; '
            'border-radius:12px; font-size:12px;">{}</span>',
            color,
            obj.get_status_display()
        )

    status_badge.short_description = 'Status Badge'


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('company', 'position', 'employment_type', 'is_current', 'order')
    list_filter = ('employment_type', 'is_current')
    list_editable = ('is_current', 'order')
    search_fields = ('company', 'position', 'description')


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('institution', 'degree_type', 'field_of_study', 'order')
    list_filter = ('degree_type', 'is_current')
    list_editable = ('order',)
    search_fields = ('institution', 'degree', 'field_of_study')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'client_title', 'rating', 'is_active', 'order')
    list_filter = ('rating', 'is_active', 'is_featured')
    list_editable = ('is_active', 'order')
    search_fields = ('client_name', 'client_title', 'content')


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'is_featured', 'order')
    list_filter = ('is_active', 'is_featured')
    list_editable = ('is_active', 'is_featured', 'order')
    search_fields = ('title', 'short_description')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_public', 'updated_at')
    list_filter = ('is_public',)