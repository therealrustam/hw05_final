from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()

    def test_index_author_tech_pages(self):
        url_list = ['/', '/about/author/', '/about/tech/']
        for url in url_list:
            response = self.guest_client.get(url)
            self.assertEqual(response.status_code, HTTPStatus.OK)


class PostsURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author_username = 'auth'
        cls.user = User.objects.create_user(username=cls.author_username)
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст',
        )
        cls.slug = 'test-slug'
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.slug,
            description='Тестовое описание',
        )

    def setUp(self):
        cache.clear()
        self.authorized_username = 'hasnoname'
        self.guest_client = Client()
        self.user = User.objects.create_user(username=self.authorized_username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.user_author = User.objects.get(username=self.author_username)
        self.author_client = Client()
        self.author_client.force_login(self.user_author)

    def test_urls_uses_correct_template_for_authorized_client(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.slug}/',
            'posts/profile.html': f'/profile/{self.authorized_username}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
            'posts/create_post.html': '/create/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.authorized_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_guest_client(self):
        templates_url_names = {
            'posts/index.html': '/',
            'posts/group_list.html': f'/group/{self.slug}/',
            'posts/profile.html': f'/profile/{self.authorized_username}/',
            'posts/post_detail.html': f'/posts/{self.post.id}/',
        }
        for template, adress in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template_for_author(self):
        template = 'posts/create_post.html'
        response = self.author_client.get(f'/posts/{self.post.id}/edit/')
        self.assertTemplateUsed(response, template)
