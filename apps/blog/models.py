from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.utils.html import strip_tags
from django.contrib.auth.models import User
from django.core.validators import MinValueValidator, MaxValueValidator
from django_resized import ResizedImageField
# from ckeditor.fields import TextField
from taggit.managers import TaggableManager
import uuid
import re


class Category(models.Model):
    """Blog post categories"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text='Font Awesome class, e.g., "fas fa-code"'
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text='Hex color, e.g., #3498db'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='children'
    )
    order = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = 'Categories'
        ordering = ['order', 'name']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['is_active']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:category', kwargs={'slug': self.slug})

    def get_post_count(self):
        """Get number of published posts in this category"""
        return self.posts.filter(
            status='published',
            is_published=True
        ).count()

    def get_all_posts(self):
        """Get all posts including subcategories"""
        categories = [self.id]
        for child in self.children.all():
            categories.append(child.id)
        return Post.objects.filter(
            category__id__in=categories,
            status='published',
            is_published=True
        )


class Tag(models.Model):
    """Custom tag model for more control"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=120, unique=True, blank=True)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name

    def get_absolute_url(self):
        return reverse('blog:tag', kwargs={'slug': self.slug})

    def get_post_count(self):
        """Get number of published posts with this tag"""
        return self.posts.filter(
            status='published',
            is_published=True
        ).count()


class PostManager(models.Manager):
    """Custom manager for Post model"""

    def published(self):
        """Get all published posts"""
        return self.filter(
            status='published',
            is_published=True,
            published_at__lte=timezone.now()
        ).select_related('author', 'category')

    def featured(self):
        """Get featured posts"""
        return self.published().filter(is_featured=True)

    def drafts(self):
        """Get draft posts"""
        return self.filter(status='draft')

    def by_category(self, category_slug):
        """Get posts by category slug"""
        return self.published().filter(category__slug=category_slug)

    def by_tag(self, tag_slug):
        """Get posts by tag slug"""
        return self.published().filter(tags__slug=tag_slug)

    def by_author(self, author_id):
        """Get posts by author"""
        return self.published().filter(author_id=author_id)

    def search(self, query):
        """Search posts"""
        return self.published().filter(
            models.Q(title__icontains=query) |
            models.Q(excerpt__icontains=query) |
            models.Q(content__icontains=query) |
            models.Q(tags__name__icontains=query) |
            models.Q(category__name__icontains=query)
        ).distinct()

    def popular(self, limit=5):
        """Get most viewed posts"""
        return self.published().order_by('-view_count')[:limit]

    def recent(self, limit=5):
        """Get most recent posts"""
        return self.published().order_by('-published_at')[:limit]

    def related(self, post, limit=3):
        """Get related posts based on tags and category"""
        return self.published().filter(
            models.Q(tags__in=post.tags.all()) |
            models.Q(category=post.category)
        ).exclude(id=post.id).distinct()[:limit]


class Post(models.Model):
    """Blog post model"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('archived', 'Archived'),
    ]

    VISIBILITY_CHOICES = [
        ('public', 'Public'),
        ('private', 'Private'),
        ('password', 'Password Protected'),
    ]

    # Basic Information
    title = models.CharField(max_length=250)
    slug = models.SlugField(max_length=300, unique=True, blank=True)
    excerpt = models.TextField(
        max_length=500,
        help_text='Short summary for listings'
    )
    content = models.TextField()

    # Media
    featured_image = ResizedImageField(
        size=[1200, 630],
        quality=85,
        upload_to='blog/featured/',
        blank=True,
        null=True,
        help_text='Recommended size: 1200x630px for social sharing'
    )
    thumbnail = ResizedImageField(
        size=[400, 300],
        quality=85,
        upload_to='blog/thumbnails/',
        blank=True,
        null=True
    )

    # Relationships
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name='blog_posts'
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        null=True,
        related_name='posts'
    )
    tags = models.ManyToManyField(
        Tag,
        blank=True,
        related_name='posts'
    )

    # Status and Visibility
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )
    visibility = models.CharField(
        max_length=20,
        choices=VISIBILITY_CHOICES,
        default='public'
    )
    password = models.CharField(
        max_length=128,
        blank=True,
        help_text='Required for password protected posts'
    )

    # Publishing
    is_published = models.BooleanField(default=False)
    is_featured = models.BooleanField(
        default=False,
        help_text='Show in featured section'
    )
    published_at = models.DateTimeField(null=True, blank=True)

    # SEO
    meta_title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Leave empty to use post title'
    )
    meta_description = models.TextField(
        max_length=300,
        blank=True,
        help_text='Leave empty to use excerpt'
    )
    meta_keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated keywords'
    )

    # Statistics
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    comment_count = models.PositiveIntegerField(default=0)

    # Reading Time
    reading_time = models.PositiveIntegerField(
        default=0,
        help_text='Estimated reading time in minutes'
    )

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    # UUID for sharing
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    # Custom manager
    objects = PostManager()

    class Meta:
        ordering = ['-published_at', '-created_at']
        indexes = [
            models.Index(fields=['status', 'is_published', 'published_at']),
            models.Index(fields=['slug']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['author', 'status']),
        ]
        get_latest_by = 'published_at'

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)

        # Calculate reading time (average reading speed: 200 words/min)
        if self.content:
            word_count = len(re.findall(r'\w+', strip_tags(self.content)))
            self.reading_time = max(1, round(word_count / 200))

        # Set published_at when first published
        if self.is_published and self.status == 'published' and not self.published_at:
            self.published_at = timezone.now()

        # Set meta title
        if not self.meta_title:
            self.meta_title = self.title

        # Set meta description
        if not self.meta_description:
            self.meta_description = self.excerpt[:300]

        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('blog:post_detail', kwargs={'slug': self.slug})

    def get_previous_post(self):
        """Get previous published post"""
        return (
            Post.objects.published()
            .filter(published_at__lt=self.published_at)
            .order_by('-published_at')
            .first()
        )

    def get_next_post(self):
        """Get next published post"""
        return (
            Post.objects.published()
            .filter(published_at__gt=self.published_at)
            .order_by('published_at')
            .first()
        )

    def get_related_posts(self, limit=3):
        """Get related posts"""
        return Post.objects.related(self, limit)

    def increment_view_count(self):
        """Increment view count atomically"""
        Post.objects.filter(pk=self.pk).update(
            view_count=models.F('view_count') + 1
        )

    def get_tags_list(self):
        """Return comma-separated tag names"""
        return ', '.join(self.tags.values_list('name', flat=True))

    def get_reading_time_display(self):
        """Display reading time"""
        if self.reading_time < 1:
            return 'Less than a minute'
        elif self.reading_time == 1:
            return '1 minute read'
        return f'{self.reading_time} minutes read'

    @property
    def is_new(self):
        """Check if post is less than 7 days old"""
        if self.published_at:
            return (timezone.now() - self.published_at).days < 7
        return False

    @property
    def excerpt_with_more(self):
        """Return excerpt with read more link"""
        if len(self.excerpt) >= 500:
            return self.excerpt[:497] + '...'
        return self.excerpt

    @classmethod
    def get_archive_dates(cls):
        """Get archive dates for sidebar"""
        return (
            cls.objects.published()
            .dates('published_at', 'month', order='DESC')
        )

    @classmethod
    def get_popular_tags(cls, limit=10):
        """Get most used tags"""
        return (
            Tag.objects
            .filter(posts__status='published', posts__is_published=True)
            .annotate(count=models.Count('posts'))
            .order_by('-count')[:limit]
        )


class Comment(models.Model):
    """Blog comments"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='comments'
    )
    parent = models.ForeignKey(
        'self',
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name='replies'
    )

    # Author Information
    name = models.CharField(max_length=100)
    email = models.EmailField()
    website = models.URLField(blank=True)

    # Comment Content
    body = models.TextField()
    is_approved = models.BooleanField(default=False)

    # Tracking
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['created_at']
        indexes = [
            models.Index(fields=['post', 'is_approved']),
            models.Index(fields=['email']),
        ]

    def __str__(self):
        return f'Comment by {self.name} on {self.post.title}'

    def approve(self):
        """Approve comment and update post comment count"""
        if not self.is_approved:
            self.is_approved = True
            self.save()
            self.post.comment_count = models.F('comment_count') + 1
            self.post.save(update_fields=['comment_count'])

    def get_replies(self):
        """Get approved replies"""
        return self.replies.filter(is_approved=True)

    @property
    def is_reply(self):
        """Check if this comment is a reply"""
        return self.parent is not None


class Subscriber(models.Model):
    """Newsletter subscribers"""
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=100, blank=True)
    is_active = models.BooleanField(default=True)
    subscribed_at = models.DateTimeField(auto_now_add=True)
    unsubscribed_at = models.DateTimeField(null=True, blank=True)

    # Tracking
    confirmation_token = models.UUIDField(
        default=uuid.uuid4,
        unique=True,
        editable=False
    )
    is_confirmed = models.BooleanField(default=False)

    class Meta:
        ordering = ['-subscribed_at']
        indexes = [
            models.Index(fields=['email']),
            models.Index(fields=['is_active', 'is_confirmed']),
        ]

    def __str__(self):
        return self.email

    def confirm(self):
        """Confirm subscription"""
        self.is_confirmed = True
        self.save(update_fields=['is_confirmed'])

    def unsubscribe(self):
        """Unsubscribe from newsletter"""
        self.is_active = False
        self.unsubscribed_at = timezone.now()
        self.save(update_fields=['is_active', 'unsubscribed_at'])


class PostView(models.Model):
    """Track post views for analytics"""
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name='post_views'
    )
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField(blank=True)
    session_key = models.CharField(max_length=40, blank=True)
    viewed_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-viewed_at']
        indexes = [
            models.Index(fields=['post', 'viewed_at']),
            models.Index(fields=['ip_address']),
        ]

    def __str__(self):
        return f'{self.ip_address} viewed {self.post.title}'

    @classmethod
    def is_unique_view(cls, post, ip_address, session_key):
        """Check if this is a unique view in last 24 hours"""
        cutoff = timezone.now() - timezone.timedelta(hours=24)
        return not cls.objects.filter(
            post=post,
            ip_address=ip_address,
            session_key=session_key,
            viewed_at__gte=cutoff
        ).exists()