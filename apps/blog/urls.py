from django.urls import path
from . import views

app_name = "blog"

urlpatterns = [
    path("", views.PostListView.as_view(), name="post_list"),
    path("post/<slug:slug>/", views.PostDetailView.as_view(), name="post_detail"),
    path("category/<slug:slug>/", views.CategoryPostListView.as_view(), name="category"),
    path("tag/<slug:slug>/", views.TagPostListView.as_view(), name="tag"),
    path("search/", views.SearchView.as_view(), name="search"),
    path("post/<slug:slug>/comment/", views.CommentCreateView.as_view(), name="add_comment"),
    path("newsletter/subscribe/", views.NewsletterSubscribeView.as_view(), name="subscribe"),
]
