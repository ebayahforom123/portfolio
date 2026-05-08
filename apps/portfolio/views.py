from django.shortcuts import render, redirect
from django.views.generic import TemplateView, ListView, DetailView, View
from django.http import JsonResponse, Http404, HttpResponse
from django.contrib import messages
from django.utils import timezone
from .models import SiteSettings, Project, Skill, SkillCategory, Experience, Technology, Testimonial


class BaseContextMixin:
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['site_settings'] = SiteSettings.objects.first()
        context['current_year'] = timezone.now().year
        return context


class HomeView(BaseContextMixin, TemplateView):
    template_name = "pages/home.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_projects'] = Project.objects.filter(is_published=True, is_featured=True)[:6]
        context['skill_categories'] = SkillCategory.objects.prefetch_related('skills').all()
        context['experiences'] = Experience.objects.filter(is_featured=True)[:3]
        return context


class AboutView(BaseContextMixin, TemplateView):
    template_name = "pages/about.html"


class ProjectListView(BaseContextMixin, ListView):
    model = Project
    template_name = "pages/projects.html"
    context_object_name = "projects"
    paginate_by = 9
    
    def get_queryset(self):
        return Project.objects.filter(is_published=True)


class ProjectDetailView(BaseContextMixin, DetailView):
    model = Project
    template_name = "pages/project_detail.html"
    context_object_name = "project"
    
    def get_queryset(self):
        return Project.objects.filter(is_published=True)


class SkillsView(BaseContextMixin, TemplateView):
    template_name = "pages/skills.html"
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['skill_categories'] = SkillCategory.objects.prefetch_related('skills').all()
        return context


class ExperienceView(BaseContextMixin, ListView):
    model = Experience
    template_name = "pages/experience.html"
    context_object_name = "experiences"
    
    def get_queryset(self):
        return Experience.objects.all().order_by('-start_date')


class ContactView(BaseContextMixin, View):
    template_name = "pages/contact.html"
    
    def get(self, request):
        return render(request, self.template_name, self.get_context_data())
    
    def post(self, request):
        name = request.POST.get('name', '')
        email = request.POST.get('email', '')
        subject = request.POST.get('subject', '')
        message = request.POST.get('message', '')
        
        if name and email and message:
            messages.success(request, 'Thank you for your message!')
        else:
            messages.error(request, 'Please fill all required fields.')
        
        return redirect('portfolio:contact')
    
    def get_context_data(self):
        return {'site_settings': SiteSettings.objects.first()}


class SearchView(BaseContextMixin, TemplateView):
    template_name = "pages/search_results.html"


class DownloadResumeView(View):
    def get(self, request):
        settings = SiteSettings.objects.first()
        if settings and settings.resume:
            response = HttpResponse(settings.resume, content_type='application/pdf')
            response['Content-Disposition'] = 'attachment; filename="Resume.pdf"'
            return response
        raise Http404("Resume not available")
