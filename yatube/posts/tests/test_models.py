from django.contrib.auth import get_user_model
from django.test import TestCase

from ..models import Group, Post

User = get_user_model()


class PostModelTest(TestCase):
    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = User.objects.create_user(username='auth')
        cls.group = Group.objects.create(
            title='test_title',
            slug='test_slug',
            description='test_description',
        )
        cls.post = Post.objects.create(
            author=cls.user,
            text='test_text_min_15_symbols',
        )

    def test_models_have_correct_object_names(self):
        """Первые пятнадцать символов поста соответствуют ожидаемым"""
        post = PostModelTest.post
        expected_object_name = post.text[:15]

        self.assertEqual(expected_object_name, str(post))

    def test_object_name_is_group_title_fild(self):
        """Название группы соответствует ожидаемому"""
        group = PostModelTest.group
        expected_object_name = group.title

        self.assertEqual(expected_object_name, str(group))

    def test_verbose_name(self):
        """Проверка verbose_name."""
        post = PostModelTest.post
        field_verboses = {
            'text': 'Текст поста',
            'pub_date': 'Дата публикации',
            'author': 'Автор',
            'group': 'Группа',
        }

        for field, expected_value in field_verboses.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).verbose_name, expected_value)

    def test_help_text(self):
        """Проверка help_text."""
        post = PostModelTest.post
        field_help_texts = {
            'text': 'Введите текст поста',
            'group': 'Группа, к которой будет относиться пост',
        }

        for field, expected_value in field_help_texts.items():
            with self.subTest(field=field):
                self.assertEqual(
                    post._meta.get_field(field).help_text, expected_value)
