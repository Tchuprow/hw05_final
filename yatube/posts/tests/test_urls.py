from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase
from posts.models import Group, Post

User = get_user_model()


class StaticURLTests(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.group = Group.objects.create(
            slug='test_slug',
        )
        cls.author = User.objects.create_user(username='test_username')
        cls.post = Post.objects.create(author=cls.author)
        cls.url_adress = {
            'home': '/',
            'group': '/group/test_slug/',
            'profile': '/profile/test_username/',
            'detail': '/posts/1/',
            'new': '/create/',
            'edit': '/posts/1/edit/',
            'comment': '/post/1/comment/',
        }

    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='HasNoName')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)
        self.authorized_author_client = Client()
        self.authorized_author_client.force_login(self.author)

    def test_all_url_exists_at_desired_location(self):
        """Страницы  доступны любому пользователю."""
        url_names = (
            self.url_adress.get('home'),
            self.url_adress.get('group'),
            self.url_adress.get('profile'),
            self.url_adress.get('detail')
        )

        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_create_url_exists_at_desired_location(self):
        """Страница  доступна авторизованому пользователю."""
        url_names = (
            self.url_adress.get('new'),
        )

        for adress in url_names:
            with self.subTest():
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_post_edit_url_exists_at_desired_location(self):
        """Страница  доступна автору поста."""
        response = self.authorized_author_client.get('/posts/1/edit/')

        self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_page_404(self):
        """Несуществующая страница."""
        response = self.guest_client.get('/unixisting_page/')

        self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
        self.assertTemplateUsed(response, 'core/404.html')

    def test_urls_author_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            self.url_adress.get('home'): 'posts/index.html',
            self.url_adress.get('group'): 'posts/group_list.html',
            self.url_adress.get('profile'): 'posts/profile.html',
            self.url_adress.get('detail'): 'posts/post_detail.html',
            self.url_adress.get('new'): 'posts/post_create.html',
            self.url_adress.get('edit'): 'posts/post_create.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_author_client.get(address)
                self.assertTemplateUsed(response, template)

    def test_urls_uses_correct_template(self):
        """Не автор поста пересылается на страницу поста."""
        response = self.authorized_client.get('/posts/1/edit/')

        self.assertRedirects(response, '/posts/1/')

    def test_create_page_url_redirect_anonymous_on_admin_login(self):
        """Страница создания поста перенаправит
        неавторизованного пользователя на страницу логина"""
        response = self.guest_client.get('/create/', follow=True)

        self.assertRedirects(
            response, '/auth/login/?next=/create/'
        )
