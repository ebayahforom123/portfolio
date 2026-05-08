from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import (
    ListView, DetailView, CreateView, UpdateView,
    DeleteView, TemplateView, View, MonthArchiveView,
    YearArchiveView, WeekArchiveView, DayArchiveView
)
from django.contrib.auth.mixins import LoginRequiredMixin, UserPassesTestMixin
from django.urls import reverse_lazy, reverse
from django.http import JsonResponse, Http404, HttpResponseRedirect
from django.db.models import Count, Q, F
from django.utils import timezone
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.core.cache import cache
from django.contrib import messages
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.contrib.sitemaps import Sitemap
from .models import Post, Category, Tag, Comment, Subscriber, PostView
from .forms import CommentForm, SearchForm, NewsletterForm
import hashlib


class BlogContextMixin:
    """Mixin to add common blog context data"""

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Sidebar data (cached for 15 minutes)
        cache_key = 'blog_sidebar_data'
        sidebar_data = cache.get(cache_key)

        if not sidebar_data:
            sidebar_data = {
                'categories': Category.objects.filter(
                    is_active=True
                ).annotate(
                    post_count=Count(
                        'posts',
                        filter=Q(posts__status='published', posts__is_published=True)
                    )
                ).filter(post_count__gt=0),
                'popular_posts': Post.objects.popular(5),
                'recent_posts': Post.objects.recent(5),
                'popular_tags': Post.get_popular_tags(15),
                'archive_dates': Post.get_archive_dates(),
            }
            cache.set(cache_key, sidebar_data, 60 * 15)

        context.update(sidebar_data)
        return context


class PostListView(BlogContextMixin, ListView):
    """Main blog listing page"""
    model = Post
    template_name = 'blog/post_list.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        return (
            Post.objects.published()
            .select_related('author', 'category')
            .prefetch_related('tags')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['featured_posts'] = Post.objects.featured()[:3]
        context['page_title'] = 'Blog'
        return context


class PostDetailView(BlogContextMixin, DetailView):
    """Single blog post detail page"""
    model = Post
    template_name = 'blog/post_detail.html'
    context_object_name = 'post'

    def get_queryset(self):
        return (
            Post.objects.published()
            .select_related('author', 'category')
            .prefetch_related('tags', 'comments')
        )

    def get_object(self, queryset=None):
        """Get post by slug or UUID"""
        if 'slug' in self.kwargs:
            return get_object_or_404(
                Post.objects.published(),
                slug=self.kwargs['slug']
            )
        elif 'uuid' in self.kwargs:
            return get_object_or_404(
                Post.objects.published(),
                uuid=self.kwargs['uuid']
            )
        raise Http404("No post found")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        post = self.object

        # Increment view count (async would be better)
        post.increment_view_count()

        # Track unique views
        self._track_view(post)

        # Get related posts
        context['related_posts'] = post.get_related_posts(3)

        # Get previous and next posts
        context['previous_post'] = post.get_previous_post()
        context['next_post'] = post.get_next_post()

        # Comments
        context['comments'] = post.comments.filter(
            is_approved=True,
            parent__isnull=True
        ).select_related('parent')

        context['comment_form'] = CommentForm()
        context['comment_count'] = post.comments.filter(is_approved=True).count()

        # SEO
        context['meta_title'] = post.meta_title or post.title
        context['meta_description'] = post.meta_description or post.excerpt
        context['meta_keywords'] = post.meta_keywords

        return context

    def _track_view(self, post):
        """Track post view for analytics"""
        request = self.request
        ip_address = self._get_client_ip()
        session_key = request.session.session_key

        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        # Only track unique views per 24 hours
        if PostView.is_unique_view(post, ip_address, session_key):
            PostView.objects.create(
                post=post,
                ip_address=ip_address,
                user_agent=request.META.get('HTTP_USER_AGENT', ''),
                session_key=session_key
            )

    def _get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR', '')


class CategoryPostListView(BlogContextMixin, ListView):
    """List posts by category"""
    model = Post
    template_name = 'blog/category_posts.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        self.category = get_object_or_404(
            Category,
            slug=self.kwargs['slug'],
            is_active=True
        )
        return (
            Post.objects.by_category(self.kwargs['slug'])
            .select_related('author', 'category')
            .prefetch_related('tags')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['category'] = self.category
        context['page_title'] = f'Category: {self.category.name}'
        return context


class TagPostListView(BlogContextMixin, ListView):
    """List posts by tag"""
    model = Post
    template_name = 'blog/tag_posts.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        self.tag = get_object_or_404(Tag, slug=self.kwargs['slug'])
        return (
            Post.objects.by_tag(self.kwargs['slug'])
            .select_related('author', 'category')
            .prefetch_related('tags')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['tag'] = self.tag
        context['page_title'] = f'Tag: {self.tag.name}'
        return context


class AuthorPostListView(BlogContextMixin, ListView):
    """List posts by author"""
    model = Post
    template_name = 'blog/author_posts.html'
    context_object_name = 'posts'
    paginate_by = 9

    def get_queryset(self):
        from django.contrib.auth.models import User
        self.author = get_object_or_404(User, id=self.kwargs['author_id'])
        return (
            Post.objects.by_author(self.kwargs['author_id'])
            .select_related('author', 'category')
            .prefetch_related('tags')
        )

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['author'] = self.author
        context['page_title'] = f'Posts by {self.author.get_full_name() or self.author.username}'
        return context


class SearchView(BlogContextMixin, ListView):
    """Search blog posts"""
    model = Post
    template_name = 'blog/search_results.html'
    context_object_name = 'posts'
    paginate_by = 12

    def get_queryset(self):
        query = self.request.GET.get('q', '').strip()
        if query:
            return Post.objects.search(query).select_related('author', 'category')
        return Post.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['query'] = self.request.GET.get('q', '')
        context['page_title'] = f'Search: {context["query"]}'
        return context


class ArchiveView(BlogContextMixin, TemplateView):
    """Blog archive page"""
    template_name = 'blog/archive.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['archive_dates'] = Post.get_archive_dates()
        context['page_title'] = 'Blog Archive'
        return context


class YearArchiveView(BlogContextMixin, YearArchiveView):
    """Posts by year"""
    model = Post
    template_name = 'blog/year_archive.html'
    date_field = 'published_at'
    make_object_list = True
    allow_future = False

    def get_queryset(self):
        return Post.objects.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = f'Posts from {self.get_year()}'
        return context


class MonthArchiveView(BlogContextMixin, MonthArchiveView):
    """Posts by month"""
    model = Post
    template_name = 'blog/month_archive.html'
    date_field = 'published_at'
    month_format = '%m'
    allow_future = False

    def get_queryset(self):
        return Post.objects.published()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = (
            f'Posts from {self.get_month_display()} {self.get_year()}'
        )
        return context


class CommentCreateView(View):
    """Handle comment creation"""

    def post(self, request, slug):
        post = get_object_or_404(Post.objects.published(), slug=slug)

        # Check if comments are allowed
        if not hasattr(settings, 'COMMENTS_ALLOWED') or not settings.COMMENTS_ALLOWED:
            messages.warning(request, 'Comments are currently disabled.')
            return redirect(post.get_absolute_url())

        form = CommentForm(request.POST)

        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.ip_address = self._get_client_ip()
            comment.user_agent = request.META.get('HTTP_USER_AGENT', '')

            # Handle reply
            parent_id = request.POST.get('parent_id')
            if parent_id:
                try:
                    comment.parent = Comment.objects.get(
                        id=parent_id,
                        post=post,
                        is_approved=True
                    )
                except Comment.DoesNotExist:
                    pass

            comment.save()

            messages.success(
                request,
                'Your comment has been submitted and is awaiting approval.'
            )
        else:
            for error in form.errors.values():
                messages.error(request, error)

        return redirect(post.get_absolute_url())

    def _get_client_ip(self):
        """Get client IP address"""
        x_forwarded_for = self.request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0].strip()
        return self.request.META.get('REMOTE_ADDR', '')


class NewsletterSubscribeView(View):
    """Handle newsletter subscription"""

    def post(self, request):
        email = request.POST.get('email', '').strip()
        name = request.POST.get('name', '').strip()

        if not email:
            messages.error(request, 'Please provide a valid email address.')
            return redirect(request.META.get('HTTP_REFERER', 'blog:post_list'))

        # Check if already subscribed
        subscriber, created = Subscriber.objects.get_or_create(
            email=email,
            defaults={'name': name}
        )

        if created:
            # Send confirmation email
            self._send_confirmation_email(subscriber, request)
            messages.success(
                request,
                'Thank you for subscribing! Please check your email to confirm.'
            )
        elif not subscriber.is_active:
            # Reactivate subscription
            subscriber.is_active = True
            subscriber.unsubscribed_at = None
            subscriber.save()
            messages.success(request, 'Your subscription has been reactivated!')
        else:
            messages.info(request, 'You are already subscribed!')

        # If AJAX request
        if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
            return JsonResponse({
                'success': True,
                'message': 'Subscription successful'
            })

        return redirect(request.META.get('HTTP_REFERER', 'blog:post_list'))

    def _send_confirmation_email(self, subscriber, request):
        """Send subscription confirmation email"""
        confirm_url = request.build_absolute_uri(
            reverse('blog:confirm_subscription', kwargs={
                'token': subscriber.confirmation_token
            })
        )

        html_message = render_to_string('emails/subscription_confirmation.html', {
            'subscriber': subscriber,
            'confirm_url': confirm_url,
        })

        try:
            send_mail(
                'Confirm your subscription',
                '',
                settings.DEFAULT_FROM_EMAIL,
                [subscriber.email],
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            print(f"Failed to send confirmation email: {e}")


class ConfirmSubscriptionView(View):
    """Confirm newsletter subscription"""

    def get(self, request, token):
        subscriber = get_object_or_404(Subscriber, confirmation_token=token)

        if subscriber.is_confirmed:
            messages.info(request, 'Your subscription is already confirmed.')
        else:
            subscriber.confirm()
            # Send welcome email
            self._send_welcome_email(subscriber)
            messages.success(request, 'Your subscription has been confirmed!')

        return redirect('blog:post_list')

    def _send_welcome_email(self, subscriber):
        """Send welcome email after confirmation"""
        html_message = render_to_string('emails/subscription_welcome.html', {
            'subscriber': subscriber,
        })

        try:
            send_mail(
                'Welcome to the newsletter!',
                '',
                settings.DEFAULT_FROM_EMAIL,
                [subscriber.email],
                html_message=html_message,
                fail_silently=True
            )
        except Exception as e:
            print(f"Failed to send welcome email: {e}")


class UnsubscribeView(View):
    """Unsubscribe from newsletter"""

    def get(self, request, email):
        subscriber = get_object_or_404(Subscriber, email=email)

        if subscriber.is_active:
            subscriber.unsubscribe()
            messages.success(request, 'You have been unsubscribed.')
        else:
            messages.info(request, 'You are already unsubscribed.')

        return redirect('blog:post_list')


class LikePostView(View):
    """Handle post likes"""

    def post(self, request, slug):
        post = get_object_or_404(Post.objects.published(), slug=slug)

        # Use session to prevent multiple likes
        liked_posts = request.session.get('liked_posts', [])

        if post.id in liked_posts:
            # Unlike
            liked_posts.remove(post.id)
            Post.objects.filter(pk=post.pk).update(
                like_count=F('like_count') - 1
            )
            liked = False
        else:
            # Like
            liked_posts.append(post.id)
            Post.objects.filter(pk=post.pk).update(
                like_count=F('like_count') + 1
            )
            liked = True

        request.session['liked_posts'] = liked_posts
        post.refresh_from_db()

        return JsonResponse({
            'liked': liked,
            'count': post.like_count
        })


class RssFeedView(View):
    """Generate RSS feed"""

    def get(self, request):
        posts = Post.objects.published()[:20]

        from django.utils.feedgenerator import Rss201rev2Feed
        feed = Rss201rev2Feed(
            title=getattr(settings, 'BLOG_TITLE', 'My Blog'),
            link=request.build_absolute_uri('/'),
            description=getattr(settings, 'BLOG_DESCRIPTION', 'Latest blog posts'),
            language='en-us',
        )

        for post in posts:
            feed.add_item(
                title=post.title,
                link=request.build_absolute_uri(post.get_absolute_url()),
                description=post.excerpt,
                author_name=post.author.get_full_name() or post.author.username,
                pubdate=post.published_at,
                categories=[tag.name for tag in post.tags.all()],
            )

        return HttpResponse(
            feed.writeString('utf-8'),
            content_type='application/rss+xml; charset=utf-8'
        )


class BlogSitemap(Sitemap):
    """Sitemap for blog"""
    changefreq = 'weekly'
    priority = 0.6

    def items(self):
        return Post.objects.published()

    def lastmod(self, obj):
        return obj.updated_at

    def location(self, obj):
        return obj.get_absolute_url()