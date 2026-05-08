from django.contrib.syndication.views import Feed
from django.utils.feedgenerator import Rss201rev2Feed
from django.urls import reverse
from .models import Post


class CorrectMimeTypeFeed(Rss201rev2Feed):
    """Override content type for RSS feed"""
    mime_type = 'application/xml'


class LatestPostsFeed(Feed):
    """RSS feed for latest blog posts"""
    feed_type = CorrectMimeTypeFeed
    title = "Latest Blog Posts"
    link = "/blog/"
    description = "Latest posts from the blog"
    author_name = "Blog Author"

    def items(self):
        return Post.objects.published()[:20]

    def item_title(self, item):
        return item.title

    def item_description(self, item):
        return item.excerpt

    def item_link(self, item):
        return item.get_absolute_url()

    def item_author_name(self, item):
        return item.author.get_full_name() or item.author.username

    def item_pubdate(self, item):
        return item.published_at

    def item_categories(self, item):
        return [tag.name for tag in item.tags.all()]

    def item_updateddate(self, item):
        return item.updated_at