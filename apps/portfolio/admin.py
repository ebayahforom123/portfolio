from django.contrib import admin
from django.utils.html import format_html
from .models import (
    SiteSettings, SkillCategory, Skill, Technology,
    Project, ProjectImage, Experience, Education,
    Testimonial, Service, Resume
)


@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Basic Information', {
            'fields': ('site_name', 'tagline', 'site_description', 'about_me', 'short_bio')
        }),
        ('Contact Information', {
            'fields': ('email', 'phone', 'location', 'availability')
        }),
        ('Social Links', {
            'fields': ('github', 'linkedin', 'twitter')
        }),
        ('Brand Assets', {
            'fields': ('profile_image', 'resume', 'favicon')
        }),
        ('SEO', {
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
    list_display = ('name', 'category', 'proficiency', 'level', 'is_featured', 'order')
    list_filter = ('category', 'level', 'is_featured')
    list_editable = ('proficiency', 'level', 'is_featured', 'order')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Technology)
class TechnologyAdmin(admin.ModelAdmin):
    list_display = ('name', 'category', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


class ProjectImageInline(admin.TabularInline):
    model = ProjectImage
    extra = 1


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    list_display = ('title', 'project_type', 'status', 'is_featured', 'is_published', 'created_at')
    list_filter = ('status', 'project_type', 'is_featured', 'is_published')
    list_editable = ('is_featured', 'is_published', 'status')
    search_fields = ('title', 'short_description')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('technologies', 'skills_demonstrated')
    inlines = [ProjectImageInline]


@admin.register(Experience)
class ExperienceAdmin(admin.ModelAdmin):
    list_display = ('company', 'position', 'employment_type', 'is_current', 'order')
    list_filter = ('employment_type', 'is_current')
    list_editable = ('is_current', 'order')
    search_fields = ('company', 'position')


@admin.register(Education)
class EducationAdmin(admin.ModelAdmin):
    list_display = ('institution', 'degree_type', 'field_of_study', 'order')
    list_editable = ('order',)
    search_fields = ('institution', 'degree')


@admin.register(Testimonial)
class TestimonialAdmin(admin.ModelAdmin):
    list_display = ('client_name', 'rating', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('client_name',)


@admin.register(Service)
class ServiceAdmin(admin.ModelAdmin):
    list_display = ('title', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    prepopulated_fields = {'slug': ('title',)}


@admin.register(Resume)
class ResumeAdmin(admin.ModelAdmin):
    list_display = ('user', 'is_public')
