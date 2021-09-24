from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Post

User = get_user_model()


class CacheTests(TestCase):

    def setUp(self):
        self.user = User.objects.create(username='test_user')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_cache_index_page(self):
        post = Post.objects.create(
            text='Новый тестовый пост',
            author=self.user,
        )
        content_new = self.authorized_client.get(
            reverse('posts:index')).content
        post.delete()
        content_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertEqual(content_new, content_delete)
        cache.clear()
        content_delete = self.authorized_client.get(
            reverse('posts:index')).content
        self.assertNotEqual(content_new, content_delete)
