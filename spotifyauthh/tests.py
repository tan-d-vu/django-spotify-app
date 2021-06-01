from django.test import TestCase, Client
from django.urls import reverse
# Create your tests here.
class HomeViewTest(TestCase):
    @classmethod
    def setUpTestData(cls):
        pass
    
    def test_view_url_exists_at_desired_location(self):
        response = self.client.get('')
        self.assertEqual(response.status_code, 200)

    def test_view_url_accessible_by_name(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)

    def test_view_uses_correct_template(self):
        response = self.client.get(reverse('home'))
        self.assertEqual(response.status_code, 200)
        self.assertTemplateUsed(response, 'spotifyauthh/home.html')

    def test_view_user_not_logged_in(self):
        response = self.client.get(reverse('home'))
        self.assertTrue(response.context == {})

    def test_view_user_logged_in(self):
        session = self.client.session
        session["token"] = "exists"
        session.save()
        response = self.client.get(reverse('home'))
        self.assertTrue(response.context["is_logged_in"] == True)
