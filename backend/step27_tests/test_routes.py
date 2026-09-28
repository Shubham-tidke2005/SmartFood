from uuid import uuid4
from django.test import SimpleTestCase
from django.urls import resolve, reverse


class VolunteerRouteTests(SimpleTestCase):
    def assert_route(self, name):
        url = reverse(f"logistics:{name}", kwargs={"task_id": uuid4()})
        self.assertEqual(resolve(url).url_name, name,
                         f"{url} is intercepted by a different URL pattern")

    def test_pickup_route(self): self.assert_route("task-pickup")
    def test_delivery_route(self): self.assert_route("task-delivery")
    def test_receipt_route(self): self.assert_route("task-receipt")
    def test_cancellation_route(self): self.assert_route("assignment-cancel")
    def test_failure_route(self): self.assert_route("task-failure")
