import shutil
import tempfile
import time

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..models import Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'auth'
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
        cls.small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        cls.uploaded = SimpleUploadedFile(
            name='small.gif',
            content=cls.small_gif,
            content_type='image/gif'
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text=cls.text,
            group=cls.group,
            image=cls.uploaded,)
        cls.post_sum = 1

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        cache.clear()
        self.user = User.objects.get(username=self.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def assert_equal_method(self, assert_dictionary):
        self.assert_dictionary = assert_dictionary
        for name, value in self.assert_dictionary.items():
            with self.subTest(name=name):
                self.assertEqual(name, value)

    def test_pages_uses_correct_template(self):
        template_edit = 'posts/create_post.html'
        template_create = 'posts/create_post.html'
        templates_pages_names = {
            'posts/index.html': reverse('posts:index'),
            'posts/group_list.html': reverse('posts:group_list',
                                             kwargs={'slug': self.slug}),
            'posts/profile.html': reverse('posts:profile',
                                          kwargs={'username': self.username}),
            'posts/post_detail.html': reverse('posts:post_detail',
                                              args=[self.post.id]),
            template_edit: reverse('posts:post_edit', args=[self.post.id]),
            template_create: reverse('posts:post_create'),
        }

        for template, reverse_name in templates_pages_names.items():
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        post_image_0 = first_object.image.name
        assert_dictionary = {
            post_text_0: self.text,
            post_author_0: self.username,
            post_group_0: self.title,
            post_image_0: f'posts/{self.uploaded.name}',
        }
        self.assert_equal_method(assert_dictionary)

    def test_group_posts_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.slug}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        second_object = response.context['group']
        group_title = second_object.title
        group_description = second_object.description
        group_slug = second_object.slug
        post_image_0 = first_object.image.name
        assert_dictionary = {
            post_text_0: self.text,
            post_author_0: self.username,
            post_group_0: self.title,
            group_title: self.title,
            group_description: self.description,
            group_slug: self.slug,
            post_image_0: f'posts/{self.uploaded.name}',
        }
        self.assert_equal_method(assert_dictionary)

    def test_profile_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.username}))
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_author_0 = first_object.author.username
        post_group_0 = first_object.group.title
        second_object = response.context['author']
        author_username_0 = second_object.username
        third_object = response.context['post_sum']
        post_image_0 = first_object.image.name
        assert_dictionary = {
            post_text_0: self.text,
            post_author_0: self.username,
            post_group_0: self.title,
            author_username_0: self.username,
            third_object: self.post_sum,
            post_image_0: f'posts/{self.uploaded.name}',
        }
        self.assert_equal_method(assert_dictionary)

    def test_post_detail_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_detail', args=[self.post.id]))
        first_object = response.context['author_one']
        author_username = first_object.username
        second_object = response.context['preview']
        third_object = response.context['post_one']
        post_text = third_object.text
        fourth_object = response.context['post_sum']
        post_image_0 = third_object.image.name
        assert_dictionary = {
            author_username: self.username,
            second_object: self.text,
            post_text: self.text,
            fourth_object: self.post_sum,
            post_image_0: f'posts/{self.uploaded.name}',
        }
        self.assert_equal_method(assert_dictionary)

    def test_create_page_show_correct_context(self):
        response = self.authorized_client.get(reverse('posts:post_create'))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)

    def test_edit_page_show_correct_context(self):
        response = self.authorized_client.get(
            reverse('posts:post_edit', args=[self.post.id]))
        form_fields = {
            'text': forms.fields.CharField,
            'group': forms.fields.ChoiceField,
        }
        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context.get('form').fields.get(value)
                self.assertIsInstance(form_field, expected)


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'auth'
        cls.user = User.objects.create_user(username=cls.username)
        cls.slug = 'test-slug'
        cls.group = Group.objects.create(
            title='Тестовая группа',
            slug=cls.slug,
            description='Тестовое описание',
        )
        for number in range(1, 13):
            exec('cls.post' + str(number) + ' = Post.objects.create('
                 'author=cls.user,'
                 f'text=f"Тестовый текст {number}",'
                 'group=cls.group,'
                 ')')

    def setUp(self):
        cache.clear()
        self.user = User.objects.get(username='auth')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_first_index_page_contains_ten_records(self):
        response = self.authorized_client.get(reverse('posts:index'))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_index_page_contains_two_records(self):
        response = self.client.get(reverse('posts:index') + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_first_group_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.slug}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_group_page_contains_two_records(self):
        response = self.client.get(reverse('posts:group_list', kwargs={
                                   'slug': self.slug}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)

    def test_first_profile_page_contains_ten_records(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.username}))
        self.assertEqual(len(response.context['page_obj']), 10)

    def test_second_profile_page_contains_two_records(self):
        response = self.client.get(reverse('posts:profile', kwargs={
                                   'username': self.username}) + '?page=2')
        self.assertEqual(len(response.context['page_obj']), 2)


class PostPagesGroupTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.username = 'auth'
        cls.user = User.objects.create_user(username=cls.username)
        cls.slug1 = 'test-slug'
        cls.group1 = Group.objects.create(
            title='Тестовая группа 1',
            slug=cls.slug1,
            description='Тестовое описание 1',
        )
        cls.slug2 = 'test-slug2'
        cls.group2 = Group.objects.create(
            title='Тестовая группа 2',
            slug=cls.slug2,
            description='Тестовое описание 2',
        )
        cls.post2 = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 2',
            group=cls.group2,
        )
        time.sleep(1)
        cls.text1 = 'Тестовый текст 1'
        cls.post1 = Post.objects.create(
            author=cls.user,
            text=cls.text1,
            group=cls.group1,
        )

    def setUp(self):
        self.user = User.objects.get(username=self.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_index_page_contains_post1(self):
        response = self.authorized_client.get(reverse('posts:index'))
        post_0 = response.context['page_obj'][0]
        text_0 = post_0.text
        self.assertEqual(text_0, self.text1)

    def test_group1_page_contains_post1(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.slug1}))
        post_0 = response.context['page_obj'][0]
        group_slug_0 = post_0.group.slug
        self.assertEqual(group_slug_0, self.slug1)

    def test_profile_page_contains_post1(self):
        response = self.authorized_client.get(
            reverse('posts:profile', kwargs={'username': self.username}))
        post_0 = response.context['page_obj'][0]
        text_0 = post_0.text
        self.assertEqual(text_0, self.text1)

    def test_group2_page_notcontains_post1(self):
        response = self.authorized_client.get(
            reverse('posts:group_list', kwargs={'slug': self.slug2}))
        post_0 = response.context['page_obj'][0]
        text_0 = post_0.text
        self.assertNotEqual(text_0, self.text1)
