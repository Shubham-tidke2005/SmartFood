from io import StringIO
from tempfile import TemporaryDirectory
from datetime import timedelta
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from django.core.files.storage import FileSystemStorage
from django.core.management import call_command
from django.test import override_settings
from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APIClient, APIRequestFactory

from apps.donations.models import Donation, DonationRequest, DonationStatusHistory
from apps.donations.serializers import DonationRevisionReadSerializer
from apps.logistics.models import VolunteerTask
from apps.moderation.models import VerificationSubmission, VerificationDocument, Complaint
from apps.moderation.audit_models import AuditEvent, OutcomeCorrection
from .factories import (
    SmartFoodAPITransactionCase,
    TEST_PASSWORD,
    api_for,
)


class PrivacyAuditTests(
    SmartFoodAPITransactionCase,
):
    def make_document(self):
        # Patch the actual field storage: PRIVATE_MEDIA_ROOT alone cannot replace
        # an already-instantiated custom storage's explicit location.
        temporary = TemporaryDirectory(prefix="smartfood-step27-documents-")
        self.addCleanup(temporary.cleanup)
        storage = FileSystemStorage(location=temporary.name)
        storage_patch = patch.object(VerificationDocument._meta.get_field("file"), "storage", storage)
        storage_patch.start()
        self.addCleanup(storage_patch.stop)
        submission = VerificationSubmission.objects.create(user=self.receiver, attempt=1)
        document = VerificationDocument(submission=submission, document_type="OTHER", original_name="synthetic.txt",
                                        mime_type="text/plain", size_bytes=14)
        document.file.save("synthetic.txt", ContentFile(b"synthetic only"), save=True)
        return document

    def test_pending_receiver_cannot_see_exact_address_in_api(self):
        donation, revision = self.make_donation()
        self.make_request(donation)
        response = api_for(self.receiver).get(reverse("donations:detail", kwargs={"donation_id": donation.pk}))
        self.assert_status(response, 200)
        self.assertNotIn(revision.pickup_address.encode(), response.content)

    def test_address_serializer_allows_only_related_parties(self):
        donation, request = self.make_allocation(mode="VOLUNTEER_DELIVERY")
        task = VolunteerTask.objects.get(donation=donation)
        task.assigned_volunteer = self.volunteer
        task.status = "ASSIGNED"
        task.save()
        # Do not reuse an ORM relation cached by the task-creation signal.
        revision = donation.revisions.select_related("donation").get(is_current=True)
        from django.contrib.auth.models import AnonymousUser
        for user, allowed in [(self.donor, True), (self.receiver, True), (self.admin, True),
                              (self.volunteer, True), (self.other_donor, False),
                              (self.other_receiver, False), (AnonymousUser(), False)]:
            with self.subTest(user=str(user)):
                http = APIRequestFactory().get("/")
                http.user = user
                data = DonationRevisionReadSerializer(revision, context={"request": http}).data
                self.assertEqual(data["pickup_address"], revision.pickup_address if allowed else None)

    def test_document_owner_and_admin_can_download_and_are_audited(self):
        document = self.make_document()
        url = reverse("moderation:document-download", kwargs={"document_id": document.pk})
        for user in (self.receiver, self.admin):
            response = api_for(user).get(url)
            try:
                self.assert_status(response, 200)
                self.assertEqual(b"".join(response.streaming_content), b"synthetic only")
                self.assertIn("no-store", response["Cache-Control"])
                self.assertEqual(response["X-Content-Type-Options"], "nosniff")
            finally:
                response.close()
        self.assertEqual(AuditEvent.objects.filter(action="DOCUMENT_DOWNLOADED", target_id=str(document.pk)).count(), 2)

    def test_another_user_cannot_download_verification_document(self):
        document = self.make_document()
        response = api_for(self.other_receiver).get(reverse("moderation:document-download", kwargs={"document_id": document.pk}))
        self.assert_status(response, 404)
        self.assertFalse(AuditEvent.objects.filter(action="DOCUMENT_DOWNLOADED").exists())

    def test_complaint_is_private_to_reporter_and_admin(self):
        complaint = Complaint.objects.create(reporter=self.receiver, subject="Synthetic complaint", description="Private test content")
        url = reverse("moderation:complaint-detail", kwargs={"complaint_id": complaint.pk})
        self.assert_status(api_for(self.other_receiver).get(url), 404)
        self.assert_status(api_for(self.admin).get(url), 200)

    def test_complaint_create_review_and_audit_journey(self):
        created = api_for(self.receiver).post(reverse("moderation:complaint-list-create"),
            {"complaint_type": "OTHER", "subject": "Synthetic test complaint", "description": "A test-only issue for review."}, format="json")
        self.assert_status(created, 201)
        url = reverse("moderation:complaint-review", kwargs={"complaint_id": created.data["id"]})
        response = api_for(self.admin).patch(url,
            {"status": "RESOLVED", "resolution": "Synthetic issue investigated and resolved."}, format="json")
        self.assert_status(response, 200)
        event = AuditEvent.objects.get(action="COMPLAINT_UPDATED", target_id=str(created.data["id"]))
        self.assertEqual(event.actor, self.admin)
        self.assertEqual(event.old_values["status"], "OPEN")
        self.assertEqual(event.new_values["status"], "RESOLVED")
        self.assertTrue(event.reason)
        self.assertIsNotNone(Complaint.objects.get(pk=created.data["id"]).resolved_at)

    def test_complaint_ui_payload_and_two_stage_admin_review(self):
        donation, _ = self.make_donation()
        created = api_for(self.donor).post(reverse("moderation:complaint-list-create"), {
            "complaint_type": "DONATION", "donation": str(donation.pk),
            "subject": "Synthetic donation issue", "description": "Test-only concern about donated food.",
        }, format="json")
        self.assert_status(created, 201)
        self.assertEqual(str(created.data["donation"]), str(donation.pk))
        url = reverse("moderation:complaint-review", kwargs={"complaint_id": created.data["id"]})
        self.assert_status(api_for(self.admin).patch(url, {
            "status": "IN_REVIEW", "audit_reason": "Started review of participant complaint.",
        }, format="json"), 200)
        self.assert_status(api_for(self.admin).patch(url, {
            "status": "RESOLVED", "resolution": "Test-only investigation completed.",
            "audit_reason": "Test-only investigation completed.",
        }, format="json"), 200)
        self.assertEqual(list(AuditEvent.objects.filter(
            action="COMPLAINT_UPDATED", target_id=str(created.data["id"])
        ).order_by("created_at").values_list("new_values__status", flat=True)),
            ["IN_REVIEW", "RESOLVED"])

    def test_non_admin_cannot_review_complaint(self):
        complaint = Complaint.objects.create(reporter=self.receiver, subject="Synthetic complaint", description="Test description")
        response = api_for(self.receiver).patch(reverse("moderation:complaint-review", kwargs={"complaint_id": complaint.pk}),
            {"status": "RESOLVED", "resolution": "Unauthorized self-resolution"}, format="json")
        self.assert_status(response, 403)
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, "OPEN")
        self.assertFalse(AuditEvent.objects.exists())

    def test_correction_requires_reason_and_retains_history(self):
        donation, _ = self.make_donation()
        donation.status = "EXPIRED"
        donation.closed_at = timezone.now() - timedelta(hours=2)
        donation.save()
        original = DonationStatusHistory.objects.create(donation=donation, actor=None, event_type="EXPIRED",
                    from_status="AVAILABLE", to_status="EXPIRED", reason="Original event")
        url = reverse("moderation:donation-outcome-correction", kwargs={"donation_id": donation.pk})
        self.assert_status(api_for(self.admin).post(url, {"new_status": "CANCELLED"}, format="json"), 400)
        self.assertFalse(OutcomeCorrection.objects.exists())
        response = api_for(self.admin).post(url, {"new_status": "CANCELLED", "reason": "Corrected after documented review"}, format="json")
        self.assert_status(response, 201)
        correction = OutcomeCorrection.objects.get(donation=donation)
        self.assertEqual((correction.old_status, correction.new_status), ("EXPIRED", "CANCELLED"))
        self.assertTrue(DonationStatusHistory.objects.filter(pk=original.pk, to_status="EXPIRED").exists())
        self.assertEqual(DonationStatusHistory.objects.filter(donation=donation, event_type="MANUAL_OUTCOME_CORRECTION").count(), 1)
        self.assertEqual(AuditEvent.objects.filter(action="OUTCOME_CORRECTED", target_id=str(donation.pk)).count(), 1)

    def test_non_admin_cannot_correct_outcome(self):
        donation, _ = self.make_donation()
        response = self.post_as(self.donor, "moderation:donation-outcome-correction", {"donation_id": donation.pk},
                                {"new_status": "CANCELLED", "reason": "Unauthorized correction"})
        self.assert_status(response, 403)
        self.assertFalse(OutcomeCorrection.objects.exists())

    def test_audit_write_failure_rolls_back_complaint_update(self):
        complaint = Complaint.objects.create(reporter=self.receiver, subject="Synthetic complaint", description="Test description")
        url = reverse("moderation:complaint-review", kwargs={"complaint_id": complaint.pk})
        with patch("apps.moderation.complaint_views.record_audit_event", side_effect=RuntimeError("audit unavailable")):
            with self.assertRaisesRegex(RuntimeError, "audit unavailable"):
                api_for(self.admin).patch(url, {"status": "RESOLVED", "resolution": "Reviewed synthetic issue"}, format="json")
        complaint.refresh_from_db()
        self.assertEqual(complaint.status, "OPEN")
        self.assertFalse(AuditEvent.objects.exists())

    def test_deactivation_preserves_history_and_rejects_existing_access_token(self):
        donation, allocation = self.make_allocation()
        history = DonationStatusHistory.objects.create(donation=donation, actor=self.receiver,
                    event_type="REQUEST_SUBMITTED", from_status="AVAILABLE", to_status="AVAILABLE")
        real_auth = APIClient()
        login = real_auth.post(reverse("accounts:login"),
            {"email": self.receiver.email, "password": TEST_PASSWORD}, format="json")
        self.assert_status(login, 200)
        real_auth.credentials(HTTP_AUTHORIZATION=f"Bearer {login.data['access']}")
        self.assert_status(real_auth.get(reverse("accounts:my-profile")), 200)
        response = self.post_as(self.admin, "moderation:participant-deactivate", {"user_id": self.receiver.pk},
                                {"reason": "Test-only account deactivation"})
        self.assert_status(response, 200)
        self.receiver.refresh_from_db()
        self.assertFalse(self.receiver.is_active)
        self.assertEqual(self.receiver.auth_version, 1)
        self.assertTrue(Donation.objects.filter(pk=donation.pk).exists())
        self.assertTrue(DonationRequest.objects.filter(pk=allocation.pk).exists())
        self.assertTrue(DonationStatusHistory.objects.filter(pk=history.pk).exists())
        self.assert_status(real_auth.get(reverse("accounts:my-profile")), 401)
        real_auth.credentials()
        # SimpleJWT's inactive-user error may be 401 or 403 depending on version;
        # either way the old refresh token must not issue a new access token.
        self.assertIn(real_auth.post(reverse("accounts:refresh"), {}, format="json").status_code, (401, 403))
        self.assertEqual(AuditEvent.objects.filter(action="ACCOUNT_DEACTIVATED", target_id=str(self.receiver.pk)).count(), 1)

    @override_settings(SMARTFOOD_RETENTION={"AUDIT_EVENT_DAYS": 30, "VERIFICATION_DOCUMENT_DAYS": 30})
    def test_retention_dry_run_and_apply_preserve_correction_and_history(self):
        donation, _ = self.make_donation()
        historical = DonationStatusHistory.objects.create(donation=donation, actor=self.donor,
            event_type="EXPIRED", from_status="AVAILABLE", to_status="EXPIRED")
        correction = OutcomeCorrection.objects.create(donation=donation, corrected_by=self.admin,
            old_status="EXPIRED", new_status="CANCELLED", reason="Historical test correction")
        protected = AuditEvent.objects.create(action="OUTCOME_CORRECTED", target_type="donations.Donation", target_id=str(donation.pk))
        expired = AuditEvent.objects.create(action="DOCUMENT_DOWNLOADED", target_type="test", target_id="expired")
        recent = AuditEvent.objects.create(action="DOCUMENT_DOWNLOADED", target_type="test", target_id="recent")
        AuditEvent.objects.filter(pk__in=[protected.pk, expired.pk]).update(created_at=timezone.now()-timedelta(days=31))
        document = self.make_document()
        VerificationSubmission.objects.filter(pk=document.submission_id).update(status="APPROVED", reviewed_at=timezone.now()-timedelta(days=31))
        storage, filename = document.file.storage, document.file.name
        call_command("purge_expired_private_data", stdout=StringIO())
        self.assertTrue(AuditEvent.objects.filter(pk=expired.pk).exists())
        self.assertTrue(storage.exists(filename))
        call_command("purge_expired_private_data", apply=True, stdout=StringIO())
        self.assertFalse(AuditEvent.objects.filter(pk=expired.pk).exists())
        self.assertFalse(VerificationDocument.objects.filter(pk=document.pk).exists())
        self.assertFalse(storage.exists(filename))
        self.assertTrue(AuditEvent.objects.filter(pk=protected.pk).exists())
        self.assertTrue(AuditEvent.objects.filter(pk=recent.pk).exists())
        self.assertTrue(OutcomeCorrection.objects.filter(pk=correction.pk).exists())
        self.assertTrue(DonationStatusHistory.objects.filter(pk=historical.pk).exists())

    def test_audit_instance_cannot_be_edited_or_deleted(self):
        event = AuditEvent.objects.create(action="COMPLAINT_UPDATED", target_type="test", target_id="test")
        with self.assertRaises(ValidationError):
            event.reason = "tampered"
            event.save()
        with self.assertRaises(ValidationError): event.delete()
        event.refresh_from_db()
        self.assertEqual(event.reason, "")
