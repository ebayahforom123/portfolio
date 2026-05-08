from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from .models import ContactMessage, ContactInfo, FAQ, QuoteRequest


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = (
        'subject', 'name', 'email', 'status', 'priority', 'created_at'
    )
    list_filter = ('status', 'priority', 'category', 'created_at', 'is_spam')
    search_fields = ('name', 'email', 'subject', 'message', 'company')
    date_hierarchy = 'created_at'
    readonly_fields = (
        'uuid', 'ip_address', 'user_agent', 'referrer',
        'session_key', 'spam_score', 'created_at', 'updated_at'
    )

    fieldsets = (
        ('Sender Information', {
            'fields': ('name', 'email', 'phone', 'company', 'website')
        }),
        ('Message Details', {
            'fields': ('subject', 'message', 'category')
        }),
        ('Status & Priority', {
            'fields': ('status', 'priority', 'is_spam', 'spam_score')
        }),
        ('Internal', {
            'fields': ('internal_notes',),
            'classes': ('collapse',)
        }),
        ('Tracking', {
            'fields': ('uuid', 'ip_address', 'user_agent', 'created_at'),
            'classes': ('collapse',)
        }),
    )

    actions = ['mark_as_read', 'mark_as_replied', 'mark_as_archived']

    @admin.action(description='Mark selected as Read')
    def mark_as_read(self, request, queryset):
        updated = queryset.filter(status='new').update(status='read')
        self.message_user(request, f'{updated} message(s) marked as read.')

    @admin.action(description='Mark selected as Replied')
    def mark_as_replied(self, request, queryset):
        updated = queryset.update(status='replied', replied_at=timezone.now())
        self.message_user(request, f'{updated} message(s) marked as replied.')

    @admin.action(description='Archive selected messages')
    def mark_as_archived(self, request, queryset):
        updated = queryset.update(status='archived')
        self.message_user(request, f'{updated} message(s) archived.')


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    fieldsets = (
        ('Primary Contact', {
            'fields': ('email', 'phone', 'whatsapp')
        }),
        ('Location', {
            'fields': ('address', 'city', 'state', 'country', 'google_maps_embed')
        }),
        ('Business Hours', {
            'fields': ('working_hours', 'timezone')
        }),
        ('Social Media', {
            'fields': ('github', 'linkedin', 'twitter', 'facebook', 'instagram', 'youtube'),
            'classes': ('collapse',)
        }),
        ('Display Settings', {
            'fields': ('show_map', 'show_social_links')
        }),
    )

    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return True

    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'is_featured', 'order')
    list_filter = ('category', 'is_active', 'is_featured')
    list_editable = ('is_active', 'is_featured', 'order')
    search_fields = ('question', 'answer')
    prepopulated_fields = {'slug': ('question',)}


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'name', 'email', 'status', 'created_at')
    list_filter = ('status', 'project_type', 'created_at')
    search_fields = ('name', 'email', 'project_name', 'company')
    date_hierarchy = 'created_at'
    readonly_fields = ('uuid', 'ip_address', 'created_at', 'updated_at')