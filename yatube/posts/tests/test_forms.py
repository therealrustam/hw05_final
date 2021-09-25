import shutil
import tempfile

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse

from ..forms import CommentForm, PostForm
from ..models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


class PostFormTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 1',
        )
        cls.form = PostForm()

    def setUp(self):
        self.user = User.objects.get(username=self.username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        post_text = 'Новый текст'
        form_data = {
            'text': post_text,
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group__slug=self.slug,
                text=post_text,
            ).exists()
        )

    def test_edit_post(self):
        post_text = 'Новый улучшенный текст'
        form_data = {
            'text': post_text,
            'group': self.group.id,
        }
        response = self.authorized_client.post(
            reverse('posts:post_edit', args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse(
            'posts:post_detail', args=[self.post.id]))
        self.assertTrue(
            Post.objects.filter(
                group__slug=self.slug,
                text=post_text,
                id=self.post.id,
            ).exists()
        )


class CommentFormTests(TestCase):
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 1',
        )
        cls.comment = Comment.objects.create(
            author=cls.user,
            post=cls.post,
            text='Тестовый комментарий 1',
        )
        cls.form = CommentForm()

    def setUp(self):
        self.authorized_username = 'hasnoname'
        self.guest_client = Client()
        self.user = User.objects.create_user(username=self.authorized_username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_authorized_client_create_comment(self):
        comment_count = Comment.objects.count()
        comment_text = 'Новый комментарий 1'
        form_data = {
            'text': comment_text,
        }
        response = self.authorized_client.post(
            reverse('posts:add_comment',
                    args=[self.post.id, ]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, reverse('posts:post_detail',
                                               args=[self.post.id]))
        self.assertEqual(Comment.objects.count(), comment_count + 1)
        self.assertTrue(
            Comment.objects.filter(
                text=comment_text,
            ).exists()
        )
        response = self.authorized_client.get(
            reverse('posts:post_detail',
                    args=[self.post.id])).context['comments'][1]
        self.assertEqual(comment_text, response.text)

    def test_guest_client_cant_create_comment(self):
        comment_count = Comment.objects.count()
        comment_text = 'Новый комментарий 2'
        form_data = {
            'text': comment_text,
        }
        response = self.guest_client.post(
            reverse('posts:add_comment',
                    args=[self.post.id]),
            data=form_data,
            follow=True,
        )
        self.assertRedirects(response, '/auth/login/?next=%2Fposts%2F1%2Fcomment%2F')
        self.assertEqual(Comment.objects.count(), comment_count)
        self.assertFalse(
            Comment.objects.filter(
                text=comment_text,
            ).exists()
        )


@ override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostFormImageTests(TestCase):
    @ classmethod
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
        cls.post = Post.objects.create(
            author=cls.user,
            text='Тестовый текст 1',
        )
        cls.form = PostForm()

    @ classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_username = 'hasnoname'
        self.user = User.objects.create_user(username=self.authorized_username)
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_create_post(self):
        post_count = Post.objects.count()
        small_gif = (
            b'\x47\x49\x46\x38\x39\x61\x02\x00'
            b'\x01\x00\x80\x00\x00\x00\x00\x00'
            b'\xFF\xFF\xFF\x21\xF9\x04\x00\x00'
            b'\x00\x00\x00\x2C\x00\x00\x00\x00'
            b'\x02\x00\x01\x00\x00\x02\x02\x0C'
            b'\x0A\x00\x3B'
        )
        uploaded = SimpleUploadedFile(
            name='small.gif',
            content=small_gif,
            content_type='image/gif'
        )
        post_text = 'Новый текст'
        form_data = {
            'text': post_text,
            'group': self.group.id,
            'image': uploaded,
        }
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True
        )
        self.assertRedirects(response, reverse(
            'posts:profile', kwargs={'username': self.authorized_username}))
        self.assertEqual(Post.objects.count(), post_count + 1)
        self.assertTrue(
            Post.objects.filter(
                group__slug=self.slug,
                text=post_text,
                image='posts/small.gif'
            ).exists()
        )
