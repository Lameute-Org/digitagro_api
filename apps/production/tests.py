from django.test import TestCase
from apps.users.models import CustomUser
from apps.production.models import Production

class ProductionTestCase(TestCase):
    def test_import(self):
        """Test que les imports fonctionnent"""
        self.assertTrue(True)
