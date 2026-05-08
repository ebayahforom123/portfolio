from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator, URLValidator
from django_resized import ResizedImageField
from ckeditor.fields import RichTextField
import uuid


class TimestampModel(models.Model):
    """Abstract base model with timestamps"""
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        abstract = True
        ordering = ['-created_at']


class SiteSettings(models.Model):
    """Global site settings - Singleton model"""
    site_name = models.CharField(max_length=100, default='My Portfolio')
    tagline = models.CharField(max_length=200, blank=True)
    site_description = models.TextField(
        help_text='Used for meta descriptions and SEO'
    )
    about_me = RichTextField(
        help_text='Detailed about me section'
    )
    short_bio = models.TextField(
        max_length=500,
        help_text='Short biography for hero section'
    )

    # Contact Information
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    availability = models.CharField(
        max_length=100,
        blank=True,
        help_text='e.g., "Available for freelance"'
    )

    # Social Links
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    stackoverflow = models.URLField(blank=True)
    medium = models.URLField(blank=True)
    youtube = models.URLField(blank=True)
    instagram = models.URLField(blank=True)

    # Brand Assets
    profile_image = ResizedImageField(
        size=[400, 400],
        quality=85,
        upload_to='profile/',
        blank=True,
        null=True
    )
    resume = models.FileField(
        upload_to='profile/',
        blank=True,
        null=True
    )
    favicon = models.ImageField(
        upload_to='profile/',
        blank=True,
        null=True
    )

    # SEO
    google_analytics_id = models.CharField(max_length=50, blank=True)
    meta_keywords = models.CharField(
        max_length=500,
        blank=True,
        help_text='Comma-separated keywords'
    )

    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'

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
        return self.site_name

    def get_social_links(self):
        """Return active social links"""
        links = {}
        social_fields = [
            'github', 'linkedin', 'twitter', 'stackoverflow',
            'medium', 'youtube', 'instagram'
        ]
        for field in social_fields:
            value = getattr(self, field)
            if value:
                links[field] = {
                    'url': value,
                    'icon': f'fab fa-{field}',
                    'name': field.capitalize()
                }
        return links


class SkillCategory(models.Model):
    """Categories for organizing skills"""
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(
        max_length=50,
        blank=True,
        help_text='Font Awesome class, e.g., "fas fa-code"'
    )
    description = models.TextField(blank=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Skill Categories'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Skill(models.Model):
    """Technical and soft skills"""
    PROFICIENCY_LEVELS = [
        ('beginner', 'Beginner'),
        ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'),
        ('expert', 'Expert'),
    ]

    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(
        SkillCategory,
        on_delete=models.CASCADE,
        related_name='skills'
    )
    proficiency = models.IntegerField(
        validators=[MinValueValidator(0), MaxValueValidator(100)],
        help_text='Percentage (0-100)'
    )
    level = models.CharField(
        max_length=20,
        choices=PROFICIENCY_LEVELS,
        default='intermediate'
    )
    icon_class = models.CharField(
        max_length=100,
        blank=True,
        help_text='Devicon or Font Awesome class'
    )
    years_of_experience = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(
        default=False,
        help_text='Show on homepage'
    )
    order = models.PositiveIntegerField(default=0)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['category__order', 'order', '-proficiency']
        indexes = [
            models.Index(fields=['category', 'proficiency']),
            models.Index(fields=['is_featured']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.category.name}-{self.name}")
        super().save(*args, **kwargs)

    def __str__(self):
        return f"{self.name} ({self.proficiency}%)"

    def get_proficiency_class(self):
        """Return CSS class based on proficiency"""
        if self.proficiency >= 90:
            return 'expert'
        elif self.proficiency >= 75:
            return 'advanced'
        elif self.proficiency >= 50:
            return 'intermediate'
        return 'beginner'

    @property
    def proficiency_label(self):
        return f"{self.get_level_display()} ({self.proficiency}%)"


class Technology(models.Model):
    """Technologies used in projects"""
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon_class = models.CharField(
        max_length=100,
        blank=True,
        help_text='Devicon class, e.g., "devicon-python-plain"'
    )
    category = models.CharField(
        max_length=50,
        choices=[
            ('language', 'Programming Language'),
            ('framework', 'Framework'),
            ('library', 'Library'),
            ('database', 'Database'),
            ('tool', 'Tool'),
            ('platform', 'Platform'),
            ('other', 'Other'),
        ],
        default='other'
    )
    color = models.CharField(
        max_length=7,
        blank=True,
        help_text='Hex color code for badges, e.g., #3498db'
    )
    is_active = models.BooleanField(default=True)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        verbose_name_plural = 'Technologies'
        ordering = ['order', 'name']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.name


class Project(TimestampModel):
    """Portfolio projects with rich details"""
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('in_progress', 'In Progress'),
        ('completed', 'Completed'),
        ('maintenance', 'Under Maintenance'),
        ('archived', 'Archived'),
    ]

    PROJECT_TYPES = [
        ('web', 'Web Application'),
        ('mobile', 'Mobile App'),
        ('desktop', 'Desktop Application'),
        ('api', 'API/Backend'),
        ('library', 'Library/Package'),
        ('design', 'UI/UX Design'),
        ('other', 'Other'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250, blank=True)
    short_description = models.CharField(
        max_length=300,
        help_text='Brief description for cards and listings'
    )
    description = RichTextField(
        help_text='Detailed project description'
    )

    # Project Details
    project_type = models.CharField(
        max_length=20,
        choices=PROJECT_TYPES,
        default='web'
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft'
    )

    # Media
    featured_image = ResizedImageField(
        size=[1200, 800],
        quality=85,
        upload_to='projects/featured/',
        blank=True,
        null=True
    )
    thumbnail = ResizedImageField(
        size=[400, 300],
        quality=85,
        upload_to='projects/thumbnails/',
        blank=True,
        null=True
    )

    # Links
    live_url = models.URLField(
        blank=True,
        help_text='Live site URL'
    )
    github_url = models.URLField(
        blank=True,
        help_text='GitHub repository URL'
    )
    documentation_url = models.URLField(blank=True)
    demo_url = models.URLField(blank=True)

    # Technical Details
    technologies = models.ManyToManyField(
        Technology,
        related_name='projects',
        blank=True
    )
    skills_demonstrated = models.ManyToManyField(
        Skill,
        related_name='projects',
        blank=True
    )

    # Project Timeline
    start_date = models.DateField(
        null=True,
        blank=True
    )
    end_date = models.DateField(
        null=True,
        blank=True
    )
    is_ongoing = models.BooleanField(default=False)

    # Display Options
    is_featured = models.BooleanField(
        default=False,
        help_text='Show on homepage'
    )
    is_published = models.BooleanField(
        default=False,
        help_text='Make visible to public'
    )
    show_in_portfolio = models.BooleanField(default=True)
    order = models.IntegerField(
        default=0,
        help_text='Display order (higher numbers first)'
    )

    # Meta Information
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)

    # Statistics (optional)
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)

    # UUID for public sharing
    uuid = models.UUIDField(
        default=uuid.uuid4,
        editable=False,
        unique=True
    )

    class Meta:
        ordering = ['-order', '-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['status', 'is_published']),
            models.Index(fields=['is_featured']),
            models.Index(fields=['slug']),
        ]

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        if not self.meta_title:
            self.meta_title = self.title
        if not self.meta_description:
            self.meta_description = self.short_description
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_absolute_url(self):
        return reverse('portfolio:project_detail', kwargs={'slug': self.slug})

    def get_technologies_list(self):
        """Return comma-separated technology names"""
        return ', '.join(self.technologies.values_list('name', flat=True))

    def get_duration(self):
        """Calculate project duration"""
        if self.start_date:
            end = self.end_date or timezone.now().date()
            duration = end - self.start_date
            months = duration.days / 30
            if months < 1:
                return f"{duration.days} days"
            elif months < 12:
                return f"{int(months)} months"
            else:
                years = months / 12
                return f"{years:.1f} years"
        return None

    def increment_view_count(self):
        """Increment project view count"""
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])

    @property
    def status_badge_class(self):
        """Return CSS class for status badge"""
        classes = {
            'draft': 'secondary',
            'in_progress': 'warning',
            'completed': 'success',
            'maintenance': 'info',
            'archived': 'dark',
        }
        return classes.get(self.status, 'secondary')


class ProjectImage(models.Model):
    """Additional images for projects"""
    project = models.ForeignKey(
        Project,
        on_delete=models.CASCADE,
        related_name='images'
    )
    image = ResizedImageField(
        size=[1920, 1080],
        quality=85,
        upload_to='projects/gallery/'
    )
    caption = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['order']

    def __str__(self):
        return f"Image for {self.project.title} - {self.order}"

    def save(self, *args, **kwargs):
        if not self.alt_text:
            self.alt_text = f"{self.project.title} - Image {self.order}"
        super().save(*args, **kwargs)


class Experience(TimestampModel):
    """Professional work experience"""
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
        ('freelance', 'Freelance'),
        ('internship', 'Internship'),
        ('volunteer', 'Volunteer'),
    ]

    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    employment_type = models.CharField(
        max_length=20,
        choices=EMPLOYMENT_TYPES,
        default='full_time'
    )
    description = RichTextField()
    achievements = models.TextField(
        blank=True,
        help_text='Key achievements (one per line)'
    )

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    # Location
    location = models.CharField(max_length=200, blank=True)
    is_remote = models.BooleanField(default=False)

    # Links
    company_url = models.URLField(blank=True)
    company_logo = ResizedImageField(
        size=[200, 200],
        quality=85,
        upload_to='experience/logos/',
        blank=True,
        null=True
    )

    # Technologies used
    technologies = models.ManyToManyField(
        Technology,
        related_name='experiences',
        blank=True
    )

    # Display
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date', 'order']
        verbose_name_plural = 'Experiences'

    def __str__(self):
        return f"{self.position} at {self.company}"

    def save(self, *args, **kwargs):
        if self.is_current:
            self.end_date = None
        super().save(*args, **kwargs)

    def get_duration_display(self):
        """Display formatted duration"""
        if self.is_current:
            return f"{self.start_date.strftime('%b %Y')} - Present"
        elif self.end_date:
            return f"{self.start_date.strftime('%b %Y')} - {self.end_date.strftime('%b %Y')}"
        return self.start_date.strftime('%b %Y')

    def get_achievements_list(self):
        """Return achievements as a list"""
        if self.achievements:
            return [a.strip() for a in self.achievements.split('\n') if a.strip()]
        return []


class Education(TimestampModel):
    """Academic education history"""
    DEGREE_TYPES = [
        ('high_school', 'High School'),
        ('associate', 'Associate Degree'),
        ('bachelor', "Bachelor's Degree"),
        ('master', "Master's Degree"),
        ('phd', 'Ph.D.'),
        ('bootcamp', 'Bootcamp'),
        ('certification', 'Certification'),
        ('other', 'Other'),
    ]

    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    degree_type = models.CharField(
        max_length=20,
        choices=DEGREE_TYPES,
        default='bachelor'
    )
    field_of_study = models.CharField(max_length=200)
    description = models.TextField(blank=True)

    # Timeline
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)

    # Performance
    gpa = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        null=True,
        blank=True,
        validators=[MinValueValidator(0), MaxValueValidator(4.0)]
    )
    achievements = models.TextField(blank=True)

    # Institution details
    institution_url = models.URLField(blank=True)
    institution_logo = ResizedImageField(
        size=[200, 200],
        quality=85,
        upload_to='education/logos/',
        blank=True,
        null=True
    )
    location = models.CharField(max_length=200, blank=True)

    # Display
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=True)

    class Meta:
        ordering = ['-start_date', 'order']
        verbose_name_plural = 'Education'

    def __str__(self):
        return f"{self.get_degree_type_display()} in {self.field_of_study} - {self.institution}"

    def get_duration_display(self):
        """Display formatted duration"""
        if self.is_current:
            return f"{self.start_date.strftime('%Y')} - Present"
        elif self.end_date:
            return f"{self.start_date.strftime('%Y')} - {self.end_date.strftime('%Y')}"
        return str(self.start_date.year)


class Testimonial(TimestampModel):
    """Client and colleague testimonials"""
    client_name = models.CharField(max_length=200)
    client_title = models.CharField(
        max_length=200,
        blank=True,
        help_text='Position or company'
    )
    client_image = ResizedImageField(
        size=[200, 200],
        quality=85,
        upload_to='testimonials/',
        blank=True,
        null=True
    )
    content = models.TextField()
    rating = models.IntegerField(
        validators=[MinValueValidator(1), MaxValueValidator(5)],
        default=5
    )

    # Source
    source = models.CharField(
        max_length=50,
        choices=[
            ('linkedin', 'LinkedIn'),
            ('google', 'Google'),
            ('direct', 'Direct'),
            ('other', 'Other'),
        ],
        default='direct'
    )
    source_url = models.URLField(blank=True)

    # Display
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']

    def __str__(self):
        return f"Testimonial from {self.client_name}"

    def get_stars(self):
        """Return list of stars for display"""
        return range(self.rating)


class Service(models.Model):
    """Services offered (for freelance portfolios)"""
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(
        max_length=50,
        help_text='Font Awesome class'
    )
    short_description = models.CharField(max_length=300)
    description = RichTextField()

    # Pricing (optional)
    price = models.DecimalField(
        max_digits=10,
        decimal_places=2,
        null=True,
        blank=True
    )
    price_unit = models.CharField(
        max_length=50,
        blank=True,
        help_text='e.g., "per hour", "per project"'
    )

    # Display
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    # Skills related to this service
    related_skills = models.ManyToManyField(
        Skill,
        blank=True,
        related_name='services'
    )

    class Meta:
        ordering = ['order', 'title']

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)

    def __str__(self):
        return self.title

    def get_price_display(self):
        """Format price display"""
        if self.price:
            price = f"${self.price:,.2f}"
            if self.price_unit:
                return f"{price} {self.price_unit}"
            return price
        return "Contact for pricing"


class Resume(models.Model):
    """Structured resume data"""
    user = models.OneToOneField(
        'auth.User',
        on_delete=models.CASCADE,
        related_name='resume'
    )
    summary = RichTextField()
    pdf_resume = models.FileField(
        upload_to='resume/',
        blank=True,
        null=True
    )

    # Contact
    website = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)

    # Display
    is_public = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Resume - {self.user.get_full_name()}"# Note: The tagline field should already be in the SiteSettings model.
# If it's missing, you need to add it manually.
