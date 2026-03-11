from django.test import TestCase
from django.core.exceptions import ValidationError
from apps.tourist_sites.models import TouristSite, TouristSiteCategory, TouristSiteImage


class TouristSiteModelTest(TestCase):
    def setUp(self):
        self.category = TouristSiteCategory.objects.create(
            name="Monuments",
            description="Sites historiques et monuments"
        )
        
    def test_tourist_site_creation(self):
        site = TouristSite.objects.create(
            name="Tour Eiffel",
            description="Monument emblématique de Paris",
            category=self.category,
            latitude=48.8584,
            longitude=2.2945
        )
        self.assertEqual(site.name, "Tour Eiffel")
        self.assertEqual(site.category, self.category)
        self.assertTrue(site.is_active)
        
    def test_tourist_site_str(self):
        site = TouristSite.objects.create(
            name="Arc de Triomphe",
            description="Monument historique",
            category=self.category,
            latitude=48.8738,
            longitude=2.2950
        )
        self.assertEqual(str(site), "Arc de Triomphe")


class TouristSiteCategoryModelTest(TestCase):
    def test_category_creation(self):
        category = TouristSiteCategory.objects.create(
            name="Musées",
            description="Musées et galeries d'art"
        )
        self.assertEqual(category.name, "Musées")
        self.assertEqual(str(category), "Musées") 