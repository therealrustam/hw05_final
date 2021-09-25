from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase
from django.urls import reverse

from ..models import Follow, Group, Post

User = get_user_model()


class FollowTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'auth'
        cls.username_one = 'david'
        cls.username_two = 'yakov'
        cls.user = User.objects.create_user(username=cls.username)
        cls.title = 'Тестовая группа'
        cls.slug = 'test-slug'
        cls.description = 'Тестовое описание'
        cls.group = Group.objects.create(
            title=cls.title,
            slug=cls.slug,
            description=cls.description,
        )
        cls.text = 'Тестовый текст'
        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.text,
            group=cls.group,
        )

    def setUp(self):
        cache.clear()
        self.guest_client = Client()
        self.user1 = User.objects.create(username=self.username_one)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user1)
        self.user2 = User.objects.create(username=self.username_two)
        self.authorized_client2 = Client()
        self.authorized_client2.force_login(self.user2)

    def test_authorized_client_can_add_follow(self):
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                    'username': self.username}),
        )
        follow_count = Follow.objects.filter(
            user=self.user1,
            author=self.user).count()
        self.assertEqual(follow_count, 1)

    def test_authorized_client_can_delete_follow(self):
        self.authorized_client.post(
            reverse('posts:profile_unfollow', kwargs={
                    'username': self.username}),
        )
        follow_count = Follow.objects.filter(
            user=self.user1, author=self.user).count()
        self.assertEqual(follow_count, 0)

    def test_new_post_follow(self):
        self.authorized_client.post(
            reverse('posts:profile_follow', kwargs={
                    'username': self.username}),
        )
        self.authorized_client2.post(
            reverse('posts:profile_follow', kwargs={
                    'username': self.username_one}),
        )
        text_old = 'Старый пост'
        Post.objects.create(
            author=self.user1,
            text=text_old,
            group=self.group,)
        text_new = 'Новый пост'
        post_new = Post.objects.create(
            author=self.user,
            text=text_new,
            group=self.group,)
        post_from_context = self.authorized_client.get(
            reverse('posts:follow_index')).context['page_obj'][0]
        self.assertEqual(post_new, post_from_context)
        post_from_context = self.authorized_client2.get(
            reverse('posts:follow_index')).context['page_obj'][0]
        self.assertNotEqual(post_new, post_from_context)
