from django.db.models.signals import post_save, pre_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings
from django.core.mail import send_mail
from django.template.loader import render_to_string
from .models import Post, Comment, Subscriber


@receiver(post_save, sender=Post)
def clear_post_cache(sender, instance, **kwargs):
    """Clear cache when a post is saved"""
    cache_keys = [
        'blog_sidebar_data',
        'homepage_data',
        'sitemap_cache',
    ]
    for key in cache_keys:
        cache.delete(key)


@receiver(post_save, sender=Comment)
def notify_admin_on_comment(sender, instance, created, **kwargs):
    """Send email notification when new comment is posted"""
    if created and not instance.is_approved:
        post = instance.post
        admin_url = f"{settings.SITE_URL}/admin/blog/comment/{instance.id}/change/"

        html_message = render_to_string('emails/new_comment_notification.html', {
            'comment': instance,
            'post': post,
            'admin_url': admin_url,
        })

        try:
            send_mail(
                f'New Comment on "{post.title}"',
                '',
                settings.DEFAULT_FROM_EMAIL,
                [admin[1] for admin in settings.ADMINS],
                html_message=html_message,
                fail_silently=True
            )
        except Exception:
            pass


@receiver(post_save, sender=Comment)
def update_comment_count(sender, instance, **kwargs):
    """Update post comment count when comment is approved"""
    if instance.is_approved:
        post = instance.post
        approved_count = post.comments.filter(is_approved=True).count()
        post.comment_count = approved_count
        post.save(update_fields=['comment_count'])


@receiver(post_save, sender=Post)
def notify_subscribers_on_new_post(sender, instance, created, **kwargs):
    """Send email notification to subscribers when new post is published"""
    if (instance.status == 'published' and
            instance.is_published and
            created):

        subscribers = Subscriber.objects.filter(
            is_active=True,
            is_confirmed=True
        )

        # Send in batches to avoid overwhelming email server
        batch_size = 50
        for i in range(0, subscribers.count(), batch_size):
            batch = subscribers[i:i + batch_size]

            for subscriber in batch:
                html_message = render_to_string('emails/new_post_notification.html', {
                    'subscriber': subscriber,
                    'post': instance,
                    'post_url': f"{settings.SITE_URL}{instance.get_absolute_url()}",
                    'unsubscribe_url': f"{settings.SITE_URL}/blog/newsletter/unsubscribe/{subscriber.email}/",
                })

                try:
                    send_mail(
                        f'New Post: {instance.title}',
                        '',
                        settings.DEFAULT_FROM_EMAIL,
                        [subscriber.email],
                        html_message=html_message,
                        fail_silently=True
                    )
                except Exception:
                    pass