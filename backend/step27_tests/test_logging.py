"""Sentinels below are synthetic strings, not passwords or real tokens."""
import logging
from django.test import SimpleTestCase
from apps.moderation.logging_filters import SensitiveDataFilter


class SensitiveLoggingTests(SimpleTestCase):
    def filtered(self, msg, args=()):
        record = logging.LogRecord("step27", logging.INFO, __file__, 1, msg, args, None)
        self.assertTrue(SensitiveDataFilter().filter(record))
        return record.getMessage()

    def test_bearer_is_redacted(self):
        self.assertNotIn("FAKE-SECRET", self.filtered("Bearer FAKE-SECRET"))

    def test_cookie_is_redacted(self):
        self.assertNotIn("FAKE-SECRET", self.filtered("sf_refresh=FAKE-SECRET; path=/"))

    def test_plain_password_is_redacted(self):
        self.assertNotIn("FAKE-SECRET", self.filtered("password=FAKE-SECRET"))

    def test_json_password_is_redacted(self):
        self.assertNotIn("FAKE-SECRET", self.filtered('{"password": "FAKE-SECRET"}'))

    def test_parameterized_log_cannot_leak_password(self):
        self.assertNotIn("FAKE-SECRET", self.filtered("password=%s", ("FAKE-SECRET",)))

    def test_structured_documents_are_redacted(self):
        self.assertNotIn("PRIVATE-CONTENT", self.filtered({"documents": ["PRIVATE-CONTENT"]}))

    def test_ordinary_log_message_still_formats(self):
        self.assertEqual(self.filtered("processed %s jobs", (3,)), "processed 3 jobs")
