import shutil
import tempfile

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.core.files.uploadedfile import SimpleUploadedFile
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from posts.models import Comment, Follow, Group, Post

User = get_user_model()
TEMP_MEDIA_ROOT = tempfile.mkdtemp(dir=settings.BASE_DIR)


@override_settings(MEDIA_ROOT=TEMP_MEDIA_ROOT)
class PostPagesTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
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
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
        )
        cls.author = User.objects.create_user(username='test_username')
        cls.post = Post.objects.create(
            author=cls.author,
            text='test_text',
            group=cls.group,
        )
        cls.group_2 = Group.objects.create(
            title='test_title_2',
            slug='test_slug_2',
        )
        cls.author_2 = User.objects.create_user(username='test_username_2')
        cls.post = Post.objects.create(
            author=cls.author_2,
            text='test_text_2',
            group=cls.group_2,
            image=uploaded,
        )
        cls.comment = Comment.objects.create(
            post=cls.post,
            author=cls.author_2,
            text='test_comment',
        )
        cls.endpoint = {
            'home': 'posts:index',
            'group': 'posts:group_list',
            'profile': 'posts:profile',
            'detail': 'posts:post_detail',
            'new': 'posts:post_create',
            'edit': 'posts:post_edit',
        }

    @classmethod
    def tearDownClass(cls):
        super().tearDownClass()
        shutil.rmtree(TEMP_MEDIA_ROOT, ignore_errors=True)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_pages_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_page_names = {
            reverse(self.endpoint.get('home')): 'posts/index.html',
            reverse(self.endpoint.get('group'), kwargs={'slug': 'test_slug'}):
            'posts/group_list.html',
            reverse(self.endpoint.get('new')): 'posts/post_create.html',
            reverse(self.endpoint.get('detail'), kwargs={'post_id': '1'}):
            'posts/post_detail.html',
            reverse(
                self.endpoint.get('profile'),
                kwargs={'username': 'test_username'}
            ):
            'posts/profile.html',
            reverse(self.endpoint.get('edit'), kwargs={'post_id': '1'}):
            'posts/post_create.html'
        }

        for reverse_name, template in templates_page_names.items():
            with self.subTest(template=template):
                response = self.authorized_client.get(reverse_name)
                self.assertTemplateUsed(response, template)

    def test_index_show_correct_context(self):
        """Шаблон index сформирован с правильным контекстом."""
        response = self.authorized_client.get(reverse('posts:index'))
        first_object = response.context['page_obj'][0]
        form_data = {
            first_object.text: 'test_text_2',
            first_object.author.username: 'test_username_2',
            first_object.group.title: 'test_title_2',
            first_object.image: 'posts/small.gif',
        }

        for context, test_context in form_data.items():
            with self.subTest(context=context):
                response = self.authorized_client.get(context)
                self.assertEqual(context, test_context)

    def test_group_pages_show_correct_context(self):
        """Шаблон group_list сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.endpoint.get('group'), kwargs={'slug': 'test_slug_2'})
        )
        first_object = response.context['group']
        post_image_0 = Post.objects.first().image
        form_data = {
            first_object.title: 'test_title_2',
            first_object.slug: 'test_slug_2',
        }

        self.assertEqual(post_image_0, 'posts/small.gif')
        for context, test_context in form_data.items():
            with self.subTest(context=context):
                response = self.authorized_client.get(context)
                self.assertEqual(context, test_context)

    def test_profile_correct_context(self):
        """Шаблон profile сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(
                self.endpoint.get('profile'),
                kwargs={'username': 'test_username_2'}
            )
        )
        first_object = response.context['page_obj'][0]
        post_text_0 = first_object.text
        post_image_0 = Post.objects.first().image

        self.assertEqual(
            response.context['author'].username, 'test_username_2'
        )
        self.assertEqual(post_text_0, 'test_text_2')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_detail_post_correct_context(self):
        """Шаблон post_detail сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.endpoint.get('detail'), kwargs={'post_id': '1'})
        )
        first_object = response.context['post']
        post_text_0 = first_object.text
        post_image_0 = Post.objects.first().image

        self.assertEqual(post_text_0, 'test_text')
        self.assertEqual(post_image_0, 'posts/small.gif')

    def test_create_show_correct_context(self):
        """Шаблон post_create сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.endpoint.get('new'))
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_edit_show_correct_context(self):
        """Шаблон post_edit сформирован с правильным контекстом."""
        response = self.authorized_client.get(
            reverse(self.endpoint.get('edit'), kwargs={'post_id': '1'})
        )
        form_fields = {
            'group': forms.fields.ChoiceField,
            'text': forms.fields.CharField,
        }

        for value, expected in form_fields.items():
            with self.subTest(value=value):
                form_field = response.context['form'].fields[value]
                self.assertIsInstance(form_field, expected)

    def test_post_another_group(self):
        """Новый пост попадает в нужную группу."""
        response = self.authorized_client.get(
            reverse(self.endpoint.get('group'), kwargs={'slug': 'test_slug'})
        )
        first_object = response.context["page_obj"][0]
        post_text_0 = first_object.text

        self.assertTrue(post_text_0, 'test_text_2')

    def test_post_in_home_and_group_and_profile(self):
        """Новый пост попадает в index, group_list, profile"""
        page_names = (
            reverse(self.endpoint.get('home')),
            reverse(
                self.endpoint.get('group'), kwargs={'slug': 'test_slug_2'}
            ),
            reverse(
                self.endpoint.get('profile'),
                kwargs={'username': 'test_username_2'}
            ),
        )

        for reverse_name in page_names:
            with self.subTest(reverse_name=reverse_name):
                response = self.authorized_client.get(reverse_name)
                first_object = response.context['page_obj'][0]
                post_text_0 = first_object.text
                self.assertEqual(post_text_0, 'test_text_2')

    def test_comment_create(self):
        """Комментарий появляется на странице"""
        response = self.authorized_client.get(
            reverse(self.endpoint.get('detail'), kwargs={'post_id': '2'})
        )
        count_comment = Comment.objects.count()

        self.assertContains(response, 'test_comment')
        self.assertEqual(count_comment, 1)

    def test_cache_index(self):
        """Проверка работы кеша"""
        response = self.authorized_client.get(
            reverse(self.endpoint.get('home'))
        )
        post = Post.objects.create(
            text='test_cache_post',
            author=self.author,
        )
        cache.clear()
        response_create_post = self.authorized_client.get(
            reverse(self.endpoint.get('home'))
        )

        self.assertNotEqual(response.content, response_create_post.content)

        post.delete()
        response_delete_post = self.authorized_client.get(
            reverse(self.endpoint.get('home'))
        )

        self.assertEqual(
            response_create_post.content, response_delete_post.content
        )

        cache.clear()
        response_clear_cache = self.authorized_client.get(
            reverse(self.endpoint.get('home'))
        )

        self.assertNotEqual(
            response_delete_post.content, response_clear_cache.content
        )


class PaginatorViewsTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.author = User.objects.create_user(username='test_name')
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
        )
        cls.posts = []
        for i in range(13):
            cls.posts.append(
                Post(
                    text=f'test_post {i}',
                    author=cls.author,
                    group=cls.group
                )
            )
        Post.objects.bulk_create(cls.posts)

    def setUp(self):
        self.authorized_client = Client()
        self.authorized_client.force_login(self.author)
        cache.clear()

    def test_first_page_contains_ten_posts(self):
        """Проверяем, что паджинатор отображает
        на первой странице 10 постов."""
        list_urls = (
            reverse('posts:index'),
            reverse('posts:group_list', kwargs={'slug': 'test_slug'}),
            reverse('posts:profile', kwargs={'username': 'test_name'}),
        )

        for tested_url in list_urls:
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context['page_obj'].object_list), 10)

    def test_second_page_contains_three_posts(self):
        """Проверяем, что оставшиеся посты отображаются на второй странице."""
        list_urls = (
            reverse('posts:index') + '?page=2',
            reverse('posts:group_list', kwargs={'slug': 'test_slug'})
            + '?page=2',
            reverse('posts:profile', kwargs={'username': 'test_name'})
            + '?page=2',
        )
        for tested_url in list_urls:
            response = self.client.get(tested_url)
            self.assertEqual(len(response.context['page_obj'].object_list), 3)


class FollowViewTest(TestCase):
    def setUp(self):
        self.client_follower = Client()
        self.client_following = Client()
        self.follower = User.objects.create_user(username='follower',)
        self.following = User.objects.create_user(username='following',)
        self.client_follower.force_login(self.follower)
        self.client_following.force_login(self.following)
        self.post = Post.objects.create(
            author=self.following,
            text='test_follow',
        )

    def test_follow(self):
        """Авторизованный пользователь может подписаться"""
        self.client_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.following.username}
            )
        )

        self.assertTrue(
            Follow.objects.filter(
                author=self.following, user=self.follower,
            ).exists()
        )

    def test_unfollow(self):
        """А также может отписаться"""
        self.client_follower.get(
            reverse(
                'posts:profile_follow',
                kwargs={'username': self.following.username}
            )
        )
        self.client_follower.get(
            reverse(
                'posts:profile_unfollow',
                kwargs={'username': self.following.username}
            )
        )

        self.assertFalse(
            Follow.objects.filter(
                author=self.following, user=self.follower,
            ).exists()
        )

    def test_subscription_feed(self):
        """Запись появляется в ленте подписчиков...или не появляется"""
        Follow.objects.create(user=self.follower,
                              author=self.following)
        response = self.client_follower.get('/follow/')
        post_text = response.context['page_obj'][0].text
        response_1 = self.client_following.get('/follow/')

        self.assertEqual(post_text, 'test_follow')
        self.assertNotContains(response_1, 'test_follow')
