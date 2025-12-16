from django.test import TestCase
from django.urls import reverse

from .models import CustomUser


class LoginFlowTests(TestCase):
    def setUp(self):
        self.user = CustomUser.objects.create_user(
            username="tester",
            email="Tester@Example.com",
            password="StrongPass123!",
        )

    def test_login_logout_and_relogin_with_username(self):
        response = self.client.post(
            reverse("login"),
            {"identifier": "tester@example.com", "password": "StrongPass123!"},
        )
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

        self.client.get(reverse("logout"))
        response = self.client.post(
            reverse("login"),
            {"identifier": "tester", "password": "StrongPass123!"},
        )
        self.assertRedirects(response, reverse("dashboard"), fetch_redirect_response=False)
        self.assertEqual(int(self.client.session["_auth_user_id"]), self.user.pk)

    def test_email_is_normalized_on_save(self):
        self.assertEqual(self.user.email, "tester@example.com")

    def test_login_rejects_invalid_password(self):
        response = self.client.post(
            reverse("login"),
            {"identifier": "tester@example.com", "password": "wrongpass"},
        )
        self.assertContains(response, "Invalid username/email or password.", status_code=200)
