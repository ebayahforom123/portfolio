from django.db import models
from django.utils import timezone
from django.core.validators import RegexValidator, EmailValidator
from django.utils.translation import gettext_lazy as _
from ckeditor.fields import RichTextField
import uuid
import json


class ContactMessage(models.Model):
    """Contact form submissions"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('read', 'Read'),
        ('replied', 'Replied'),
        ('archived', 'Archived'),
        ('spam', 'Spam'),
    ]

    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]

    # Sender Information
    name = models.CharField(max_length=200, verbose_name=_('Full Name'))
    email = models.EmailField(verbose_name=_('Email Address'))
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Phone Number'),
        validators=[
            RegexValidator(
                regex=r'^\+?1?\d{9,15}$',
                message='Phone number must be in international format. e.g., +1234567890'
            )
        ]
    )
    company = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Company/Organization')
    )
    website = models.URLField(blank=True, verbose_name=_('Website'))

    # Message Details
    subject = models.CharField(max_length=300, verbose_name=_('Subject'))
    message = models.TextField(verbose_name=_('Message'))

    # Metadata
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new',
        verbose_name=_('Status')
    )
    priority = models.CharField(
        max_length=10,
        choices=PRIORITY_CHOICES,
        default='normal',
        verbose_name=_('Priority')
    )

    # Categories (for organizing inquiries)
    CATEGORY_CHOICES = [
        ('general', 'General Inquiry'),
        ('project', 'Project Proposal'),
        ('collaboration', 'Collaboration'),
        ('freelance', 'Freelance Work'),
        ('job', 'Job Opportunity'),
        ('bug', 'Bug Report'),
        ('feature', 'Feature Request'),
        ('support', 'Support'),
        ('other', 'Other'),
    ]
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name=_('Category')
    )

    # Budget Information (for project inquiries)
    BUDGET_CHOICES = [
        ('not_specified', 'Not Specified'),
        ('under_1k', 'Under $1,000'),
        ('1k_5k', '$1,000 - $5,000'),
        ('5k_10k', '$5,000 - $10,000'),
        ('10k_25k', '$10,000 - $25,000'),
        ('25k_50k', '$25,000 - $50,000'),
        ('over_50k', 'Over $50,000'),
    ]
    budget_range = models.CharField(
        max_length=20,
        choices=BUDGET_CHOICES,
        default='not_specified',
        blank=True,
        verbose_name=_('Budget Range')
    )

    # Timeline
    TIMELINE_CHOICES = [
        ('not_specified', 'Not Specified'),
        ('immediate', 'Immediate'),
        ('1_2_weeks', '1-2 Weeks'),
        ('1_month', '1 Month'),
        ('1_3_months', '1-3 Months'),
        ('3_6_months', '3-6 Months'),
        ('flexible', 'Flexible'),
    ]
    timeline = models.CharField(
        max_length=20,
        choices=TIMELINE_CHOICES,
        default='not_specified',
        blank=True,
        verbose_name=_('Timeline')
    )

    # Attachments (optional)
    attachment = models.FileField(
        upload_to='contact/attachments/%Y/%m/',
        blank=True,
        null=True,
        verbose_name=_('Attachment'),
        help_text=_('Upload any relevant files (max 5MB)')
    )

    # Tracking Information
    ip_address = models.GenericIPAddressField(
        null=True,
        blank=True,
        verbose_name=_('IP Address')
    )
    user_agent = models.TextField(
        blank=True,
        verbose_name=_('User Agent')
    )
    referrer = models.URLField(
        blank=True,
        verbose_name=_('Referrer URL')
    )
    session_key = models.CharField(
        max_length=40,
        blank=True,
        verbose_name=_('Session Key')
    )

    # Response Tracking
    replied_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Replied At')
    )
    replied_by = models.ForeignKey(
        'auth.User',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='replied_messages',
        verbose_name=_('Replied By')
    )
    reply_notes = models.TextField(
        blank=True,
        verbose_name=_('Reply Notes')
    )

    # Internal Notes
    internal_notes = models.TextField(
        blank=True,
        verbose_name=_('Internal Notes'),
        help_text=_('Admin notes (not visible to sender)')
    )

    # Spam Detection
    is_spam = models.BooleanField(
        default=False,
        verbose_name=_('Is Spam')
    )
    spam_score = models.FloatField(
        default=0.0,
        verbose_name=_('Spam Score')
    )

    # Email Tracking
    email_sent = models.BooleanField(
        default=False,
        verbose_name=_('Auto-reply Sent')
    )
    email_sent_at = models.DateTimeField(
        null=True,
        blank=True,
        verbose_name=_('Auto-reply Sent At')
    )

    # UUID for tracking
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True,
        verbose_name=_('UUID')
    )

    # Timestamps
    created_at = models.DateTimeField(
        auto_now_add=True,
        verbose_name=_('Received At')
    )
    updated_at = models.DateTimeField(
        auto_now=True,
        verbose_name=_('Last Updated')
    )

    class Meta:
        verbose_name = _('Contact Message')
        verbose_name_plural = _('Contact Messages')
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['status', 'priority']),
            models.Index(fields=['email']),
            models.Index(fields=['created_at']),
            models.Index(fields=['category']),
        ]

    def __str__(self):
        return f'{self.subject} - {self.name} ({self.email})'

    def save(self, *args, **kwargs):
        # Run spam detection
        if not self.pk:  # Only on creation
            self.spam_score = self._calculate_spam_score()
            self.is_spam = self.spam_score > 0.7

        super().save(*args, **kwargs)

    def _calculate_spam_score(self):
        """Basic spam detection algorithm"""
        score = 0.0

        # Check for common spam indicators
        spam_keywords = [
            'viagra', 'cialis', 'casino', 'lottery', 'winner',
            'click here', 'buy now', 'free money', 'act now',
            'limited time', 'guaranteed', 'credit card', 'seo services'
        ]

        content = f"{self.subject} {self.message}".lower()

        # Count spam keywords
        keyword_count = sum(1 for keyword in spam_keywords if keyword in content)
        score += keyword_count * 0.15

        # Check for excessive links
        import re
        urls = re.findall(r'https?://\S+', self.message)
        if len(urls) > 3:
            score += 0.3

        # Check for ALL CAPS subject
        if self.subject.isupper():
            score += 0.2

        # Check for excessive exclamation marks
        if self.message.count('!') > 5:
            score += 0.1

        # Check message to link ratio
        if self.website and len(self.message) < 100:
            score += 0.2

        return min(score, 1.0)

    def mark_as_read(self):
        """Mark message as read"""
        if self.status == 'new':
            self.status = 'read'
            self.save(update_fields=['status', 'updated_at'])

    def mark_as_replied(self, user=None, notes=''):
        """Mark message as replied"""
        self.status = 'replied'
        self.replied_at = timezone.now()
        self.replied_by = user
        if notes:
            self.reply_notes = notes
        self.save()

    def mark_as_archived(self):
        """Archive message"""
        self.status = 'archived'
        self.save(update_fields=['status', 'updated_at'])

    def mark_as_spam(self):
        """Mark as spam"""
        self.status = 'spam'
        self.is_spam = True
        self.save()

    def get_reply_url(self):
        """Generate mailto URL for quick reply"""
        import urllib.parse
        params = {
            'subject': f'Re: {self.subject}',
            'body': f'Dear {self.name},\n\n',
        }
        return f'mailto:{self.email}?{urllib.parse.urlencode(params)}'

    @property
    def is_new(self):
        return self.status == 'new'

    @property
    def formatted_created_at(self):
        """Return formatted date"""
        return self.created_at.strftime('%B %d, %Y at %I:%M %p')

    @classmethod
    def get_unread_count(cls):
        """Get count of unread messages"""
        return cls.objects.filter(status='new').count()

    @classmethod
    def get_stats(cls):
        """Get message statistics"""
        return {
            'total': cls.objects.count(),
            'new': cls.objects.filter(status='new').count(),
            'read': cls.objects.filter(status='read').count(),
            'replied': cls.objects.filter(status='replied').count(),
            'archived': cls.objects.filter(status='archived').count(),
            'spam': cls.objects.filter(status='spam').count(),
            'today': cls.objects.filter(
                created_at__date=timezone.now().date()
            ).count(),
        }


class ContactInfo(models.Model):
    """Contact information settings - Singleton"""

    # Primary Contact
    email = models.EmailField(
        verbose_name=_('Primary Email'),
        help_text=_('Main contact email address')
    )
    phone = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('Phone Number')
    )
    whatsapp = models.CharField(
        max_length=20,
        blank=True,
        verbose_name=_('WhatsApp Number')
    )

    # Location
    address = models.TextField(
        blank=True,
        verbose_name=_('Physical Address')
    )
    city = models.CharField(max_length=100, blank=True)
    state = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Map
    latitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Latitude')
    )
    longitude = models.DecimalField(
        max_digits=9,
        decimal_places=6,
        null=True,
        blank=True,
        verbose_name=_('Longitude')
    )
    google_maps_embed = models.TextField(
        blank=True,
        verbose_name=_('Google Maps Embed Code'),
        help_text=_('Paste Google Maps iframe embed code here')
    )

    # Business Hours
    working_hours = models.TextField(
        blank=True,
        verbose_name=_('Working Hours'),
        help_text=_('e.g., Monday - Friday: 9:00 AM - 6:00 PM')
    )
    timezone = models.CharField(
        max_length=50,
        default='UTC',
        blank=True,
        verbose_name=_('Timezone')
    )

    # Social Media Links
    github = models.URLField(blank=True, verbose_name=_('GitHub'))
    linkedin = models.URLField(blank=True, verbose_name=_('LinkedIn'))
    twitter = models.URLField(blank=True, verbose_name=_('Twitter'))
    facebook = models.URLField(blank=True, verbose_name=_('Facebook'))
    instagram = models.URLField(blank=True, verbose_name=_('Instagram'))
    youtube = models.URLField(blank=True, verbose_name=_('YouTube'))
    medium = models.URLField(blank=True, verbose_name=_('Medium'))
    dev_to = models.URLField(blank=True, verbose_name=_('Dev.to'))
    stackoverflow = models.URLField(blank=True, verbose_name=_('Stack Overflow'))
    codepen = models.URLField(blank=True, verbose_name=_('CodePen'))
    dribbble = models.URLField(blank=True, verbose_name=_('Dribbble'))
    behance = models.URLField(blank=True, verbose_name=_('Behance'))
    discord = models.URLField(blank=True, verbose_name=_('Discord'))
    telegram = models.URLField(blank=True, verbose_name=_('Telegram'))

    # Messaging Platforms
    skype = models.CharField(max_length=100, blank=True, verbose_name=_('Skype'))
    slack = models.CharField(max_length=100, blank=True, verbose_name=_('Slack Workspace'))

    # Form Settings
    use_recaptcha = models.BooleanField(
        default=False,
        verbose_name=_('Use reCAPTCHA'),
        help_text=_('Enable Google reCAPTCHA for contact form')
    )
    recaptcha_site_key = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('reCAPTCHA Site Key')
    )
    recaptcha_secret_key = models.CharField(
        max_length=100,
        blank=True,
        verbose_name=_('reCAPTCHA Secret Key')
    )

    # Email Settings
    auto_reply_enabled = models.BooleanField(
        default=True,
        verbose_name=_('Auto-reply Enabled'),
        help_text=_('Send automatic confirmation email to sender')
    )
    auto_reply_subject = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Auto-reply Subject'),
        default='Thank you for your message'
    )
    auto_reply_message = RichTextField(
        blank=True,
        verbose_name=_('Auto-reply Message'),
        help_text=_('Leave empty to use default message')
    )

    # Notification Settings
    notify_admin = models.BooleanField(
        default=True,
        verbose_name=_('Notify Admin'),
        help_text=_('Send email notification on new messages')
    )
    notification_email = models.EmailField(
        blank=True,
        verbose_name=_('Notification Email'),
        help_text=_('Email to receive notifications (leave empty for primary email)')
    )

    # Display Settings
    show_contact_form = models.BooleanField(
        default=True,
        verbose_name=_('Show Contact Form')
    )
    show_map = models.BooleanField(
        default=True,
        verbose_name=_('Show Map')
    )
    show_social_links = models.BooleanField(
        default=True,
        verbose_name=_('Show Social Links')
    )

    # SEO
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        verbose_name=_('Meta Title')
    )
    meta_description = models.TextField(
        max_length=300,
        blank=True,
        verbose_name=_('Meta Description')
    )

    # Timestamps
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('Contact Information')
        verbose_name_plural = _('Contact Information')

    def save(self, *args, **kwargs):
        """Ensure only one instance exists"""
        self.pk = 1
        super().save(*args, **kwargs)

    @classmethod
    def load(cls):
        """Get the singleton instance"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj

    def __str__(self):
        return f'Contact Information ({self.email})'

    def get_social_links(self):
        """Return list of active social media links"""
        links = []
        social_fields = {
            'github': ('fab fa-github', 'GitHub'),
            'linkedin': ('fab fa-linkedin', 'LinkedIn'),
            'twitter': ('fab fa-twitter', 'Twitter'),
            'facebook': ('fab fa-facebook', 'Facebook'),
            'instagram': ('fab fa-instagram', 'Instagram'),
            'youtube': ('fab fa-youtube', 'YouTube'),
            'medium': ('fab fa-medium', 'Medium'),
            'dev_to': ('fab fa-dev', 'Dev.to'),
            'stackoverflow': ('fab fa-stack-overflow', 'Stack Overflow'),
            'codepen': ('fab fa-codepen', 'CodePen'),
            'dribbble': ('fab fa-dribbble', 'Dribbble'),
            'behance': ('fab fa-behance', 'Behance'),
            'discord': ('fab fa-discord', 'Discord'),
            'telegram': ('fab fa-telegram', 'Telegram'),
        }

        for field, (icon, name) in social_fields.items():
            url = getattr(self, field, None)
            if url:
                links.append({
                    'name': name,
                    'url': url,
                    'icon': icon,
                    'field': field,
                })

        return links

    def has_social_links(self):
        """Check if any social links are set"""
        return len(self.get_social_links()) > 0


class FAQ(models.Model):
    """Frequently Asked Questions"""

    question = models.CharField(max_length=300, verbose_name=_('Question'))
    slug = models.SlugField(max_length=350, unique=True, blank=True)
    answer = RichTextField(verbose_name=_('Answer'))

    # Categorization
    CATEGORY_CHOICES = [
        ('general', 'General'),
        ('services', 'Services'),
        ('pricing', 'Pricing'),
        ('technical', 'Technical'),
        ('process', 'Process'),
        ('other', 'Other'),
    ]
    category = models.CharField(
        max_length=20,
        choices=CATEGORY_CHOICES,
        default='general',
        verbose_name=_('Category')
    )

    # Display
    is_active = models.BooleanField(
        default=True,
        verbose_name=_('Active')
    )
    is_featured = models.BooleanField(
        default=False,
        verbose_name=_('Featured'),
        help_text=_('Show at top of list')
    )
    order = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Order')
    )

    # Helpful tracking
    helpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Helpful Count')
    )
    not_helpful_count = models.PositiveIntegerField(
        default=0,
        verbose_name=_('Not Helpful Count')
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = _('FAQ')
        verbose_name_plural = _('FAQs')
        ordering = ['-is_featured', 'order', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'category']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            from django.utils.text import slugify
            self.slug = slugify(self.question)[:350]
        super().save(*args, **kwargs)

    def __str__(self):
        return self.question

    def get_absolute_url(self):
        from django.urls import reverse
        return f"{reverse('contact:faq')}#faq-{self.slug}"

    @property
    def helpful_percentage(self):
        """Calculate helpful percentage"""
        total = self.helpful_count + self.not_helpful_count
        if total == 0:
            return 0
        return round((self.helpful_count / total) * 100, 1)


class QuoteRequest(models.Model):
    """Project quote requests"""
    STATUS_CHOICES = [
        ('new', 'New'),
        ('reviewing', 'Reviewing'),
        ('quoted', 'Quoted'),
        ('accepted', 'Accepted'),
        ('declined', 'Declined'),
        ('archived', 'Archived'),
    ]

    # Contact Information
    name = models.CharField(max_length=200)
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    company = models.CharField(max_length=200, blank=True)

    # Project Details
    project_name = models.CharField(max_length=300)
    project_type = models.CharField(max_length=50, choices=[
        ('web', 'Web Application'),
        ('mobile', 'Mobile App'),
        ('desktop', 'Desktop Application'),
        ('api', 'API Development'),
        ('ecommerce', 'E-commerce'),
        ('cms', 'Content Management System'),
        ('redesign', 'Website Redesign'),
        ('consulting', 'Consulting'),
        ('other', 'Other'),
    ])
    project_description = models.TextField()

    # Technical Requirements
    technologies = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated preferred technologies'
    )
    has_design = models.BooleanField(
        default=False,
        help_text='Do you have designs ready?'
    )

    # Budget and Timeline
    budget_range = models.CharField(
        max_length=20,
        choices=ContactMessage.BUDGET_CHOICES,
        default='not_specified'
    )
    timeline = models.CharField(
        max_length=20,
        choices=ContactMessage.TIMELINE_CHOICES,
        default='not_specified'
    )

    # Status
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='new'
    )

    # Attachments
    attachment = models.FileField(
        upload_to='quotes/attachments/%Y/%m/',
        blank=True,
        null=True
    )

    # Response
    quote_amount = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    quote_notes = models.TextField(blank=True)
    quoted_at = models.DateTimeField(null=True, blank=True)

    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)

    class Meta:
        verbose_name = _('Quote Request')
        verbose_name_plural = _('Quote Requests')
        ordering = ['-created_at']

    def __str__(self):
        return f'Quote: {self.project_name} - {self.name}'