from tests.system.base_test import BaseTest


class TestParticleHubApp(BaseTest):

    def test_root(self):
        with self.app() as client:
            response = client.get('/')
            self.assertEqual(response.status_code, 200)

    def test_add_device(self):
        # TODO: test CSRF !
        self.fail()
