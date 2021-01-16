from unittest import TestCase
from particlehub.models import ParticleCloud


class TestParticleCloud(TestCase):

    def test_create_cloud(self):
        cloud = ParticleCloud(cloud_api_token="abc123")
        self.assertEqual(cloud.cloud_api_token, "abc123", "Cloud API token not equal to the constructor argument")
