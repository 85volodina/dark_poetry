from django.contrib.auth import get_user_model
from django.test import Client, TestCase

User = get_user_model()


class ProfileTest(TestCase):
    def setUp(self):
        self.client_not_auth = Client()
        self.user = User.objects.create_user(
            username="kotik", email="mrrr@gmail.com", password="12345"
        )

    def test_profile(self):
        response = self.client_not_auth.get("/kotik/")
        self.assertEqual(response.status_code, 200)
        self.assertIsInstance(response.context["author"], User)
        self.assertEqual(
            response.context["author"].username, self.user.username
        )
