from http import HTTPStatus

from django.test import Client, TestCase


class NotFoundURLTests(TestCase):

    def setUp(self):
        self.guest_client = Client()

    def test_urls_uses_correct_template_for_404(self):
        templates_url_names = {
            '/nonexisting_page/': 'core/404.html',
            '/group/error/': 'core/404.html',
        }
        for adress, template in templates_url_names.items():
            with self.subTest(adress=adress):
                response = self.guest_client.get(adress)
                self.assertTemplateUsed(response, template)
                self.assertEqual(response.status_code, HTTPStatus.NOT_FOUND)
