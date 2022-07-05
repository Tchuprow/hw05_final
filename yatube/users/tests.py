from http import HTTPStatus

from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class UsersURLTests(TestCase):
    def setUp(self):
        self.guest_client = Client()
        self.user = User.objects.create_user(username='test_name')
        self.authorized_client = Client()
        self.authorized_client.force_login(self.user)

    def test_guest_page(self):
        """Страницы доступны для неавторизованного пользователя."""
        url_names = {
            '/auth/login/',
            '/auth/logout/',
            '/auth/signup/',
            '/auth/password_reset/done/',
            '/auth/reset/done/',
        }

        for adress in url_names:
            with self.subTest():
                response = self.guest_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_authorized_page(self):
        """Страницы доступны для авторизованного пользователя."""
        url_names = {
            '/auth/password_change/',
            '/auth/password_change/done/',
            '/auth/password_reset/',
        }

        for adress in url_names:
            with self.subTest():
                response = self.authorized_client.get(adress)
                self.assertEqual(response.status_code, HTTPStatus.OK)

    def test_redirect_anonymous_on_admin_login(self):
        """Страницы перенаправят неавторизованного
        пользователя на страницу логина"""
        url_name = {
            '/auth/password_change/':
            '/auth/login/?next=/auth/password_change/',
            '/auth/password_change/done/':
            '/auth/login/?next=/auth/password_change/done/',
        }

        for address, redirect_address in url_name.items():
            with self.subTest(address=address):
                response = self.guest_client.get(address)
                self.assertRedirects(response, redirect_address)

    def test_urls_uses_correct_template(self):
        """URL-адрес использует соответствующий шаблон."""
        templates_url_names = {
            '/auth/login/': 'users/login.html',
            '/auth/signup/': 'users/signup.html',
            '/auth/password_reset/done/': 'users/password_reset_done.html',
            '/auth/reset/done/': 'users/password_reset_complete.html',
            '/auth/password_change/': 'users/password_change_form.html',
            '/auth/password_change/done/': 'users/password_change_done.html',
            '/auth/password_reset/': 'users/password_reset_form.html',
            '/auth/logout/': 'users/logged_out.html',
        }

        for address, template in templates_url_names.items():
            with self.subTest(address=address):
                response = self.authorized_client.get(address)
                self.assertTemplateUsed(response, template)
