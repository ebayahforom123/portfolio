from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from .models import Category, Tag, Post, Comment, Subscriber, PostView


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active', 'order')
    list_filter = ('is_active',)
    list_editable = ('is_active', 'order')
    search_fields = ('name', 'description')
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ('name', 'slug', 'is_active')
    list_filter = ('is_active',)
    list_editable = ('is_active',)
    search_fields = ('name',)
    prepopulated_fields = {'slug': ('name',)}


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = (
        'title', 'author', 'category', 'status', 'status_badge',
        'is_featured', 'is_published', 'published_at', 'view_count', 'comment_count'
    )
    list_filter = ('status', 'is_published', 'is_featured', 'category', 'tags', 'author')
    list_editable = ('is_featured', 'is_published', 'status')
    search_fields = ('title', 'content', 'excerpt', 'tags__name')
    prepopulated_fields = {'slug': ('title',)}
    filter_horizontal = ('tags',)
    date_hierarchy = 'published_at'

    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'slug', 'excerpt', 'content')
        }),
        ('Media', {
            'fields': ('featured_image', 'thumbnail')
        }),
        ('Relationships', {
            'fields': ('author', 'category', 'tags')
        }),
        ('Status & Visibility', {
            'fields': ('status', 'visibility', 'is_published', 'is_featured')
        }),
        ('Publishing', {
            'fields': ('published_at',)
        }),
        ('SEO', {
            'fields': ('meta_title', 'meta_description', 'meta_keywords'),
            'classes': ('collapse',)
        }),
    )

    readonly_fields = ('view_count', 'like_count', 'comment_count', 'reading_time', 'uuid')

    def status_badge(self, obj):
        colors = {
            'draft': '#95a5a6',
            'published': '#27ae60',
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

    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.author = request.user
        super().save_model(request, obj, form, change)


@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('name', 'email', 'is_approved', 'created_at')
    list_filter = ('is_approved', 'created_at')
    list_editable = ('is_approved',)
    search_fields = ('name', 'email', 'body', 'post__title')
    date_hierarchy = 'created_at'


@admin.register(Subscriber)
class SubscriberAdmin(admin.ModelAdmin):
    list_display = ('email', 'name', 'is_active', 'is_confirmed', 'subscribed_at')
    list_filter = ('is_active', 'is_confirmed', 'subscribed_at')
    list_editable = ('is_active',)
    search_fields = ('email', 'name')
    date_hierarchy = 'subscribed_at'


@admin.register(PostView)
class PostViewAdmin(admin.ModelAdmin):
    list_display = ('post', 'ip_address', 'viewed_at')
    list_filter = ('viewed_at',)
    search_fields = ('post__title', 'ip_address')
    date_hierarchy = 'viewed_at'
    readonly_fields = ('post', 'ip_address', 'user_agent', 'session_key', 'viewed_at')

    def has_add_permission(self, request):
        return False

    def has_change_permission(self, request, obj=None):
        return False