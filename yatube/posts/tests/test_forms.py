import shutil
import tempfile
from http import HTTPStatus

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostCreateFormTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
        )

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.guest_client = Client()
        self.author = User.objects.create_user(username='test_username')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)

    def test_post_create(self):
        """Проверка создания новой записи в базе данных."""
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
        form_data = {
            'text': 'test_text',
            'group': self.group.id,
            'image': uploaded,
        }
        count_posts = Post.objects.count()
        response = self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )

        self.assertTrue(
            Post.objects.filter(
                text='test_text',
                group='1',
                image='posts/small.gif',
            ).exists()
        )
        self.assertEqual(self.author.username, 'test_username')
        self.assertEqual(Post.objects.count(), count_posts + 1)
        self.assertRedirects(
            response,
            reverse('posts:profile', kwargs={'username': 'test_username'})
        )

    def test_authorized_edit_post(self):
        """Проверка изменения поста с задданым id"""
        form_data = {
            'text': 'test_text',
            'group': self.group.id,
        }
        self.authorized_client.post(
            reverse('posts:post_create'),
            data=form_data,
            follow=True,
        )
        form_data = {
            'text': 'test_text_edit',
            'group': self.group.id,
        }

        post_2 = Post.objects.get(id=self.group.id)
        count_posts = Post.objects.count()
        response_edit = self.authorized_client.post(
            reverse('posts:post_edit', kwargs={'post_id': post_2.id}),
            data=form_data,
            follow=True,
        )
        post_2 = Post.objects.get(id=self.group.id)

        self.assertEqual(Post.objects.count(), count_posts)
        self.assertEqual(self.author.username, 'test_username')
        self.assertEqual(response_edit.status_code, HTTPStatus.OK)
        self.assertTrue(
            Post.objects.filter(
                text='test_text_edit',
                group='1',
            ).exists()
        )

    def test_guest_not_can_add_comment(self):
        """Гость не может оставлять комментарии"""
        user = User.objects.create_user(username='comment_user')
        post = Post.objects.create(text='text', author=user)
        form_data = {'text': 'test_comment', }
        self.authorized_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )
        form_data = {'text': 'test_comment_2', }
        self.guest_client.post(
            reverse('posts:add_comment', kwargs={'post_id': post.id}),
            data=form_data,
            follow=True,
        )

        self.assertFalse(
            Comment.objects.filter(text='test_comment_2', ).exists()
        )
        self.assertTrue(
            Comment.objects.filter(text='test_comment', ).exists()
        )
