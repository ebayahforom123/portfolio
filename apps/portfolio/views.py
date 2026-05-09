from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView, View
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib import messages
from django.utils import timezone
from .models import (
    SiteSettings, Project, Skill, SkillCategory, 
    Experience, Technology, Testimonial
)


class BaseContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['site_settings'] = SiteSettings.objects.first()
        except:
            context['site_settings'] = {'site_name': 'Kiros'}
        context['current_year'] = timezone.now().year
        return context


class HomeView(BaseContextMixin, TemplateView):
    template_name = "pages/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['featured_projects'] = Project.objects.filter(
                is_published=True, is_featured=True
            ).prefetch_related('technologies')[:6]
            context['skill_categories'] = SkillCategory.objects.prefetch_related('skills').all()
            context['experiences'] = Experience.objects.filter(is_featured=True)[:3]
        except:
            pass
        return context


class AboutView(BaseContextMixin, TemplateView):
    template_name = "pages/about.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['experiences'] = Experience.objects.filter(is_featured=True)
            context['skill_categories'] = SkillCategory.objects.prefetch_related('skills').all()
        except:
            pass
        return context


class ProjectListView(BaseContextMixin, ListView):
    model = Project
    template_name = "pages/projects.html"
    context_object_name = "projects"
    paginate_by = 9
    
    def get_queryset(self):
        try:
            return Project.objects.filter(is_published=True).prefetch_related('technologies')
        except:
            return Project.objects.none()


class ProjectDetailView(BaseContextMixin, DetailView):
    model = Project
    template_name = "pages/project_detail.html"
    context_object_name = "project"
    
    def get_queryset(self):
        try:
            return Project.objects.filter(is_published=True)
        except:
            return Project.objects.none()


class SkillsView(BaseContextMixin, TemplateView):
    template_name = "pages/skills.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        try:
            context['skill_categories'] = SkillCategory.objects.prefetch_related('skills').all()
        except:
            pass
        return context


class ExperienceView(BaseContextMixin, ListView):
    model = Experience
    template_name = "pages/experience.html"
    context_object_name = "experiences"
    
    def get_queryset(self):
        try:
            return Experience.objects.all().order_by('-start_date')
        except:
            return Experience.objects.none()


class ContactView(BaseContextMixin, View):
    """Contact form - handles GET and POST, saves to database"""
    template_name = "pages/contact.html"
    
    def get(self, request):
        context = self.get_context_data()
        return render(request, self.template_name, context)
    
    def post(self, request):
        name = request.POST.get('name', '').strip()
        email = request.POST.get('email', '').strip()
        subject = request.POST.get('subject', '').strip()
        msg_text = request.POST.get('message', '').strip()
        
        # Validate
        errors = []
        if not name:
            errors.append('Please enter your name.')
        if not email:
            errors.append('Please enter your email.')
        if not msg_text:
            errors.append('Please enter a message.')
        elif len(msg_text) < 10:
            errors.append('Message must be at least 10 characters.')
        
        if errors:
            for error in errors:
                messages.error(request, error)
            return redirect('portfolio:contact')
        
        # SAVE TO DATABASE
        try:
            from apps.contact.models import ContactMessage
            
            contact_msg = ContactMessage.objects.create(
                name=name,
                email=email,
                subject=subject or 'No Subject',
                message=msg_text,
                ip_address=self._get_client_ip(request),
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
            )
            
            print(f"✅ Message saved! ID: {contact_msg.id}")
            print(f"   From: {name} ({email})")
            print(f"   Subject: {subject}")
            
            messages.success(request, '✅ Thank you for your message! I will get back to you soon.')
            
        except Exception as e:
            print(f"❌ Error saving message: {e}")
            # Still show success to user even if save fails
            messages.success(request, 'Thank you for your message! I will get back to you soon.')
        
        return redirect('portfolio:contact')
    
    def get_context_data(self):
        return {
            'site_settings': SiteSettings.objects.first(),
            'current_year': timezone.now().year,
        }
    
    def _get_client_ip(self, request):
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return request.META.get('REMOTE_ADDR', '')


class SearchView(BaseContextMixin, TemplateView):
    template_name = "pages/search_results.html"


class DownloadResumeView(View):
    def get(self, request):
        try:
            settings = SiteSettings.objects.first()
            if settings and settings.resume:
                response = HttpResponse(settings.resume, content_type='application/pdf')
                response['Content-Disposition'] = 'attachment; filename="Resume.pdf"'
                return response
        except:
            pass
        raise Http404("Resume not available")
