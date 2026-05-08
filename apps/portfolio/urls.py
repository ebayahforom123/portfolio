from django.urls import path
from . import views

app_name = "portfolio"

urlpatterns = [
    path("", views.HomeView.as_view(), name="home"),
    path("about/", views.AboutView.as_view(), name="about"),
    path("projects/", views.ProjectListView.as_view(), name="projects"),
    path("projects/<slug:slug>/", views.ProjectDetailView.as_view(), name="project_detail"),
    path("skills/", views.SkillsView.as_view(), name="skills"),
    path("experience/", views.ExperienceView.as_view(), name="experience"),
    path("contact/", views.ContactView.as_view(), name="contact"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("download-resume/", views.DownloadResumeView.as_view(), name="download_resume"),
]
