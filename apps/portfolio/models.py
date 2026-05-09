from django.db import models
from django.urls import reverse
from django.utils.text import slugify
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator
from django_resized import ResizedImageField
import uuid


class SiteSettings(models.Model):
    site_name = models.CharField(max_length=100, default='My Portfolio')
    tagline = models.CharField(max_length=200, blank=True)
    site_description = models.TextField(help_text='Used for meta descriptions and SEO')
    about_me = models.TextField(help_text='Detailed about me section', blank=True)
    short_bio = models.TextField(max_length=500, help_text='Short biography for hero section', blank=True)
    
    email = models.EmailField()
    phone = models.CharField(max_length=20, blank=True)
    location = models.CharField(max_length=200, blank=True)
    availability = models.CharField(max_length=100, blank=True)
    
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    
    profile_image = ResizedImageField(size=[400, 400], quality=85, upload_to='profile/', blank=True, null=True)
    resume = models.FileField(upload_to='profile/', blank=True, null=True)
    favicon = models.ImageField(upload_to='profile/', blank=True, null=True)
    
    google_analytics_id = models.CharField(max_length=50, blank=True)
    meta_keywords = models.CharField(max_length=500, blank=True)
    
    class Meta:
        verbose_name = 'Site Settings'
        verbose_name_plural = 'Site Settings'
    
    def save(self, *args, **kwargs):
        self.pk = 1
        super().save(*args, **kwargs)
    
    @classmethod
    def load(cls):
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def __str__(self):
        return self.site_name


class SkillCategory(models.Model):
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50, blank=True)
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
    name = models.CharField(max_length=100)
    slug = models.SlugField(unique=True, blank=True)
    category = models.ForeignKey(SkillCategory, on_delete=models.CASCADE, related_name='skills')
    proficiency = models.IntegerField(validators=[MinValueValidator(0), MaxValueValidator(100)])
    level = models.CharField(max_length=20, choices=[
        ('beginner', 'Beginner'), ('intermediate', 'Intermediate'),
        ('advanced', 'Advanced'), ('expert', 'Expert'),
    ], default='intermediate')
    icon_class = models.CharField(max_length=100, blank=True)
    years_of_experience = models.PositiveIntegerField(default=0)
    description = models.TextField(blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['category__order', 'order', '-proficiency']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(f"{self.category.name}-{self.name}")
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"{self.name} ({self.proficiency}%)"


class Technology(models.Model):
    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(unique=True, blank=True)
    icon_class = models.CharField(max_length=100, blank=True)
    category = models.CharField(max_length=50, choices=[
        ('language', 'Programming Language'), ('framework', 'Framework'),
        ('library', 'Library'), ('database', 'Database'),
        ('tool', 'Tool'), ('platform', 'Platform'), ('other', 'Other'),
    ], default='other')
    color = models.CharField(max_length=7, blank=True)
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


class Project(models.Model):
    STATUS_CHOICES = [
        ('draft', 'Draft'), ('in_progress', 'In Progress'),
        ('completed', 'Completed'), ('maintenance', 'Under Maintenance'),
        ('archived', 'Archived'),
    ]
    PROJECT_TYPES = [
        ('web', 'Web Application'), ('mobile', 'Mobile App'),
        ('desktop', 'Desktop Application'), ('api', 'API/Backend'),
        ('library', 'Library/Package'), ('design', 'UI/UX Design'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, max_length=250, blank=True)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    
    project_type = models.CharField(max_length=20, choices=PROJECT_TYPES, default='web')
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    featured_image = ResizedImageField(size=[1200, 800], quality=85, upload_to='projects/featured/', blank=True, null=True)
    thumbnail = ResizedImageField(size=[400, 300], quality=85, upload_to='projects/thumbnails/', blank=True, null=True)
    
    live_url = models.URLField(blank=True)
    github_url = models.URLField(blank=True)
    documentation_url = models.URLField(blank=True)
    demo_url = models.URLField(blank=True)
    
    technologies = models.ManyToManyField(Technology, related_name='projects', blank=True)
    skills_demonstrated = models.ManyToManyField(Skill, related_name='projects', blank=True)
    
    start_date = models.DateField(null=True, blank=True)
    end_date = models.DateField(null=True, blank=True)
    is_ongoing = models.BooleanField(default=False)
    
    is_featured = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    show_in_portfolio = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    
    meta_title = models.CharField(max_length=200, blank=True)
    meta_description = models.TextField(max_length=300, blank=True)
    
    view_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)
    
    uuid = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-order', '-is_featured', '-created_at']
    
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
    
    def increment_view_count(self):
        self.view_count = models.F('view_count') + 1
        self.save(update_fields=['view_count'])


class ProjectImage(models.Model):
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = ResizedImageField(size=[1920, 1080], quality=85, upload_to='projects/gallery/')
    caption = models.CharField(max_length=200, blank=True)
    alt_text = models.CharField(max_length=200, blank=True)
    is_featured = models.BooleanField(default=False)
    order = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['order']
    
    def __str__(self):
        return f"Image for {self.project.title}"


class Experience(models.Model):
    EMPLOYMENT_TYPES = [
        ('full_time', 'Full Time'), ('part_time', 'Part Time'),
        ('contract', 'Contract'), ('freelance', 'Freelance'),
        ('internship', 'Internship'), ('volunteer', 'Volunteer'),
    ]
    
    company = models.CharField(max_length=200)
    position = models.CharField(max_length=200)
    employment_type = models.CharField(max_length=20, choices=EMPLOYMENT_TYPES, default='full_time')
    description = models.TextField()
    achievements = models.TextField(blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    location = models.CharField(max_length=200, blank=True)
    is_remote = models.BooleanField(default=False)
    
    company_url = models.URLField(blank=True)
    company_logo = ResizedImageField(size=[200, 200], quality=85, upload_to='experience/logos/', blank=True, null=True)
    
    technologies = models.ManyToManyField(Technology, related_name='experiences', blank=True)
    
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
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
        if self.is_current:
            return f"{self.start_date.strftime('%b %Y')} - Present"
        elif self.end_date:
            return f"{self.start_date.strftime('%b %Y')} - {self.end_date.strftime('%b %Y')}"
        return self.start_date.strftime('%b %Y')


class Education(models.Model):
    DEGREE_TYPES = [
        ('high_school', 'High School'), ('associate', 'Associate Degree'),
        ('bachelor', "Bachelor's Degree"), ('master', "Master's Degree"),
        ('phd', 'Ph.D.'), ('bootcamp', 'Bootcamp'),
        ('certification', 'Certification'), ('other', 'Other'),
    ]
    
    institution = models.CharField(max_length=200)
    degree = models.CharField(max_length=200)
    degree_type = models.CharField(max_length=20, choices=DEGREE_TYPES, default='bachelor')
    field_of_study = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    
    start_date = models.DateField()
    end_date = models.DateField(null=True, blank=True)
    is_current = models.BooleanField(default=False)
    
    gpa = models.DecimalField(max_digits=3, decimal_places=2, null=True, blank=True)
    achievements = models.TextField(blank=True)
    
    institution_url = models.URLField(blank=True)
    institution_logo = ResizedImageField(size=[200, 200], quality=85, upload_to='education/logos/', blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    
    order = models.IntegerField(default=0)
    is_featured = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date', 'order']
        verbose_name_plural = 'Education'
    
    def __str__(self):
        return f"{self.get_degree_type_display()} in {self.field_of_study} - {self.institution}"


class Testimonial(models.Model):
    client_name = models.CharField(max_length=200)
    client_title = models.CharField(max_length=200, blank=True)
    client_image = ResizedImageField(size=[200, 200], quality=85, upload_to='testimonials/', blank=True, null=True)
    content = models.TextField()
    rating = models.IntegerField(validators=[MinValueValidator(1), MaxValueValidator(5)], default=5)
    
    source = models.CharField(max_length=50, choices=[
        ('linkedin', 'LinkedIn'), ('google', 'Google'),
        ('direct', 'Direct'), ('other', 'Other'),
    ], default='direct')
    source_url = models.URLField(blank=True)
    
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', 'order', '-created_at']
    
    def __str__(self):
        return f"Testimonial from {self.client_name}"


class Service(models.Model):
    title = models.CharField(max_length=200)
    slug = models.SlugField(unique=True, blank=True)
    icon = models.CharField(max_length=50)
    short_description = models.CharField(max_length=300)
    description = models.TextField()
    
    price = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    price_unit = models.CharField(max_length=50, blank=True)
    
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    order = models.IntegerField(default=0)
    
    related_skills = models.ManyToManyField(Skill, blank=True, related_name='services')
    
    class Meta:
        ordering = ['order', 'title']
    
    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.title)
        super().save(*args, **kwargs)
    
    def __str__(self):
        return self.title


class Resume(models.Model):
    user = models.OneToOneField('auth.User', on_delete=models.CASCADE, related_name='resume')
    summary = models.TextField()
    pdf_resume = models.FileField(upload_to='resume/', blank=True, null=True)
    
    website = models.URLField(blank=True)
    github = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    
    is_public = models.BooleanField(default=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Resume - {self.user.get_full_name()}"
