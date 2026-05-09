from django.contrib import admin
from django.utils.html import format_html
from django.utils import timezone
from django.contrib import messages as django_messages
from django.core.mail import send_mail
from django.conf import settings
from django.http import HttpResponseRedirect
from django.urls import path, reverse
from .models import ContactMessage, ContactInfo, FAQ, QuoteRequest


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ('subject', 'name', 'email', 'status_badge', 'quick_actions', 'created_at')
    list_filter = ('status', 'category', 'created_at')
    search_fields = ('name', 'email', 'subject', 'message')
    date_hierarchy = 'created_at'
    readonly_fields = ('uuid', 'ip_address', 'created_at', 'updated_at', 'reply_section')
    
    fieldsets = (
        ('Sender Information', {
            'fields': ('name', 'email', 'phone', 'company')
        }),
        ('Message', {
            'fields': ('subject', 'message', 'category')
        }),
        ('Reply Section', {
            'fields': ('reply_section',),
            'description': 'Use the reply form below to send an email response'
        }),
        ('Status & Notes', {
            'fields': ('status', 'internal_notes', 'reply_notes')
        }),
        ('Tracking', {
            'fields': ('uuid', 'ip_address', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
    
    actions = ['mark_read', 'mark_replied', 'mark_archived']
    
    def status_badge(self, obj):
        colors = {
            'new': '#3498db',
            'read': '#95a5a6',
            'replied': '#27ae60',
            'archived': '#7f8c8d',
            'spam': '#e74c3c',
        }
        color = colors.get(obj.status, '#95a5a6')
        return format_html(
            '<span style="background:{};color:white;padding:4px 12px;'
            'border-radius:12px;font-size:12px;">{}</span>',
            color, obj.get_status_display()
        )
    status_badge.short_description = 'Status'
    
    def quick_actions(self, obj):
        """Show action buttons"""
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={obj.email}&su=Re: {obj.subject}"
        outlook_url = f"https://outlook.live.com/mail/0/deeplink/compose?to={obj.email}&subject=Re: {obj.subject}"
        
        return format_html(
            '<div style="display:flex;gap:5px;flex-wrap:wrap;">'
            '<a href="{}" target="_blank" style="background:#DB4437;color:white;padding:4px 10px;'
            'border-radius:5px;text-decoration:none;font-size:12px;">📧 Gmail</a>'
            '<a href="{}" target="_blank" style="background:#0072C6;color:white;padding:4px 10px;'
            'border-radius:5px;text-decoration:none;font-size:12px;">📧 Outlook</a>'
            '<a href="mailto:{}?subject=Re: {}&body=Dear {}," style="background:#2563eb;color:white;'
            'padding:4px 10px;border-radius:5px;text-decoration:none;font-size:12px;">📧 Email App</a>'
            '</div>',
            gmail_url, outlook_url, obj.email, obj.subject, obj.name
        )
    quick_actions.short_description = 'Quick Reply'
    
    def reply_section(self, obj):
        """Show reply information and links"""
        if not obj.email:
            return format_html('<p>No email address available.</p>')
        
        gmail_url = f"https://mail.google.com/mail/?view=cm&fs=1&to={obj.email}&su=Re: {obj.subject}&body=Dear {obj.name},%0D%0A%0D%0A"
        outlook_url = f"https://outlook.live.com/mail/0/deeplink/compose?to={obj.email}&subject=Re: {obj.subject}"
        yahoo_url = f"https://compose.mail.yahoo.com/?to={obj.email}&subject=Re: {obj.subject}"
        
        return format_html(
            '<div style="background:#f8f9fa;padding:20px;border-radius:10px;border:2px solid #2563eb;">'
            '<h3 style="color:#2563eb;">📧 Reply to: {}</h3>'
            '<p><strong>Email:</strong> {}</p>'
            '<p><strong>Subject:</strong> Re: {}</p>'
            '<hr>'
            '<p style="font-weight:bold;">Click below to reply:</p>'
            '<div style="display:flex;gap:10px;flex-wrap:wrap;margin:15px 0;">'
            '<a href="{}" target="_blank" style="background:#DB4437;color:white;padding:12px 24px;'
            'border-radius:8px;text-decoration:none;font-size:16px;font-weight:bold;">'
            '📧 Open Gmail</a>'
            '<a href="{}" target="_blank" style="background:#0072C6;color:white;padding:12px 24px;'
            'border-radius:8px;text-decoration:none;font-size:16px;font-weight:bold;">'
            '📧 Open Outlook</a>'
            '<a href="{}" target="_blank" style="background:#720e9e;color:white;padding:12px 24px;'
            'border-radius:8px;text-decoration:none;font-size:16px;font-weight:bold;">'
            '📧 Open Yahoo</a>'
            '</div>'
            '<p style="margin-top:15px;color:#666;">Or manually copy the email and reply from your email client.</p>'
            '</div>',
            obj.name, obj.email, obj.subject,
            gmail_url, outlook_url, yahoo_url
        )
    reply_section.short_description = 'Reply Options'
    
    def response_change(self, request, obj):
        """After saving, redirect back with a message"""
        if "_reply" in request.POST:
            # Mark as replied
            obj.status = 'replied'
            obj.replied_at = timezone.now()
            obj.save()
            django_messages.success(request, f'Message marked as replied! Reply to {obj.email}')
        return super().response_change(request, obj)
    
    @admin.action(description='Mark as Read')
    def mark_read(self, request, queryset):
        queryset.update(status='read')
        django_messages.success(request, f'{queryset.count()} messages marked as read.')
    
    @admin.action(description='Mark as Replied')
    def mark_replied(self, request, queryset):
        queryset.update(status='replied', replied_at=timezone.now())
        django_messages.success(request, f'{queryset.count()} messages marked as replied.')
    
    @admin.action(description='Archive messages')
    def mark_archived(self, request, queryset):
        queryset.update(status='archived')
        django_messages.success(request, f'{queryset.count()} messages archived.')


@admin.register(ContactInfo)
class ContactInfoAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        if self.model.objects.exists():
            return False
        return True
    
    def has_delete_permission(self, request, obj=None):
        return False


@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ('question', 'category', 'is_active', 'order')
    list_editable = ('is_active', 'order')
    search_fields = ('question', 'answer')
    prepopulated_fields = {'slug': ('question',)}


@admin.register(QuoteRequest)
class QuoteRequestAdmin(admin.ModelAdmin):
    list_display = ('project_name', 'name', 'email', 'status', 'created_at')
    list_filter = ('status',)
    search_fields = ('name', 'email', 'project_name')
    date_hierarchy = 'created_at'
