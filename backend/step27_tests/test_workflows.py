from decimal import Decimal

from django.urls import reverse

from apps.donations.models import Donation, DonationRequest, DonationStatusHistory
from apps.logistics.models import HandoverRecord, ReceiptConfirmation, VolunteerTask
from apps.receivers.models import ReceiverRequirement, ReceiverAvailability
from .factories import SmartFoodAPICase, api_for


class DonationWorkflowTests(SmartFoodAPICase):
    def test_expired_donation_rejects_request_without_reservation(self):
        donation, _ = self.make_donation(expired=True)
        response = self.post_as(self.receiver, "donations:request-create", {"donation_id": donation.pk},
                                {"proposed_mode": "RECEIVER_COLLECTION"})
        self.assert_status(response, 409)
        donation.refresh_from_db()
        self.assertEqual(donation.status, "EXPIRED")
        self.assertFalse(DonationRequest.objects.filter(donation=donation).exists())
        self.assertEqual(ReceiverRequirement.objects.get(receiver=self.receiver).quantity_reserved, 0)

    def test_another_donor_cannot_edit_listing(self):
        donation, revision = self.make_donation()
        response = self.post_as(self.other_donor, "donations:revision-create", {"donation_id": donation.pk},
                                self.payload(food_name="Unauthorized overwrite"))
        self.assert_status(response, 403)
        revision.refresh_from_db()
        self.assertNotEqual(revision.food_name, "Unauthorized overwrite")
        self.assertEqual(donation.revisions.count(), 1)

    def test_approval_rechecks_changed_availability(self):
        donation, _ = self.make_donation()
        submitted = self.post_as(self.receiver, "donations:request-create", {"donation_id": donation.pk},
                                 {"proposed_mode": "RECEIVER_COLLECTION"})
        self.assert_status(submitted, 201)
        ReceiverAvailability.objects.filter(receiver=self.receiver).update(active=False)
        response = self.post_as(self.donor, "donations:request-approve", {"request_id": submitted.data["id"]})
        self.assert_status(response, 409)
        self.assertFalse(response.data["eligibility_checks"]["receiving_available"])
        self.assertEqual(ReceiverRequirement.objects.get(receiver=self.receiver).quantity_reserved, 0)

    def test_pickup_retry_does_not_create_second_handover_or_history(self):
        donation, _ = self.make_allocation()
        kwargs = {"donation_id": donation.pk}
        first = self.post_as(self.donor, "logistics:handover-confirm", kwargs, {"actual_quantity": "20.000"})
        self.assert_status(first, 201)
        second = self.post_as(self.donor, "logistics:handover-confirm", kwargs, {"actual_quantity": "20.000"})
        self.assert_status(second, 409)
        self.assertEqual(HandoverRecord.objects.filter(donation=donation).count(), 1)
        self.assertEqual(DonationStatusHistory.objects.filter(donation=donation, event_type="HANDOVER_CONFIRMED").count(), 1)

    def test_receipt_is_restricted_to_approved_receiver(self):
        donation, _ = self.make_delivered()
        response = self.post_as(self.other_receiver, "logistics:receipt-confirm", {"donation_id": donation.pk},
                                {"accepted_quantity": "20.000"})
        self.assert_status(response, 403)
        self.assertFalse(ReceiptConfirmation.objects.filter(donation=donation).exists())

    def test_rejected_delivery_contributes_no_successful_impact(self):
        donation, _ = self.make_delivered()
        response = self.post_as(self.receiver, "logistics:receipt-confirm", {"donation_id": donation.pk},
                                {"accepted_quantity": "0.000", "discrepancy_type": "QUALITY",
                                 "discrepancy_notes": "Test only: all items rejected."})
        self.assert_status(response, 201)
        donation.refresh_from_db()
        self.assertEqual(donation.status, "FAILED")
        self.assertEqual(ReceiptConfirmation.objects.get(donation=donation).accepted_quantity, 0)
        for user in (self.donor, self.receiver, self.admin):
            with self.subTest(role=user.role):
                analytics = api_for(user).get("/api/analytics/")
                self.assert_status(analytics, 200)
                self.assertEqual(analytics.data["quantity_redistributed"], [])

    def test_direct_collection_complete_api_journey(self):
        created = api_for(self.donor).post(reverse("donations:list-create"), self.payload(), format="json")
        self.assert_status(created, 201)
        donation_id = created.data["id"]
        submitted = self.post_as(self.receiver, "donations:request-create", {"donation_id": donation_id},
                                 {"proposed_mode": "RECEIVER_COLLECTION"})
        self.assert_status(submitted, 201)
        self.assert_status(self.post_as(self.donor, "donations:request-approve", {"request_id": submitted.data["id"]}), 200)
        requirement = ReceiverRequirement.objects.get(receiver=self.receiver)
        self.assertEqual(requirement.quantity_reserved, Decimal("20.000"))
        self.assert_status(self.post_as(self.donor, "logistics:handover-confirm", {"donation_id": donation_id},
                                        {"actual_quantity": "20.000"}), 201)
        receipt = self.post_as(self.receiver, "logistics:receipt-confirm", {"donation_id": donation_id},
                               {"accepted_quantity": "18.000", "discrepancy_type": "SHORTAGE",
                                "discrepancy_notes": "Test only: two portions not accepted."})
        self.assert_status(receipt, 201)
        self.assertEqual(Donation.objects.get(pk=donation_id).status, "COMPLETED")
        requirement.refresh_from_db()
        self.assertEqual(requirement.quantity_reserved, 0)
        before = list(DonationStatusHistory.objects.filter(donation_id=donation_id).values_list("id", flat=True))
        self.assert_status(self.post_as(self.receiver, "logistics:receipt-confirm", {"donation_id": donation_id},
                                        {"accepted_quantity": "18.000"}), 409)
        self.assertEqual(ReceiptConfirmation.objects.filter(donation_id=donation_id).count(), 1)
        self.assertEqual(set(before), set(DonationStatusHistory.objects.filter(donation_id=donation_id).values_list("id", flat=True)))
        donor_analytics = api_for(self.donor).get("/api/analytics/")
        self.assert_status(donor_analytics, 200)
        self.assertEqual(donor_analytics.data["summary"]["completed_donations"], 1)
        self.assertEqual({r["unit"]: Decimal(r["quantity"]) for r in donor_analytics.data["quantity_redistributed"]},
                         {"PORTION": Decimal("18.000")})

    def test_volunteer_transport_complete_api_journey(self):
        created = api_for(self.donor).post(reverse("donations:list-create"), self.payload(), format="json")
        self.assert_status(created, 201)
        donation_id = created.data["id"]
        submitted = self.post_as(self.receiver, "donations:request-create", {"donation_id": donation_id},
                                 {"proposed_mode": "VOLUNTEER_DELIVERY"})
        self.assert_status(submitted, 201)
        self.assert_status(self.post_as(self.donor, "donations:request-approve", {"request_id": submitted.data["id"]}), 200)
        task = VolunteerTask.objects.get(donation_id=donation_id)
        receiver_requests = api_for(self.receiver).get(reverse("donations:request-list"))
        self.assert_status(receiver_requests, 200)
        self.assertEqual(str(receiver_requests.data[0]["volunteer_task_id"]), str(task.pk))
        self.assert_status(self.post_as(self.volunteer, "logistics:task-accept", {"task_id": task.pk}), 200)
        self.assert_status(self.post_as(self.volunteer, "logistics:task-pickup", {"task_id": task.pk},
                                        {"actual_quantity": "20.000"}), 200)
        self.assert_status(self.post_as(self.volunteer, "logistics:task-delivery", {"task_id": task.pk},
                                        {"actual_quantity": "20.000"}), 200)
        task.refresh_from_db()
        self.assertEqual(task.status, "DELIVERED")
        self.assertEqual(Donation.objects.get(pk=donation_id).status, "DELIVERED")
        self.assertFalse(ReceiptConfirmation.objects.filter(donation_id=donation_id).exists())
        self.assertEqual(api_for(self.donor).get("/api/analytics/").data["quantity_redistributed"], [])
        self.assert_status(self.post_as(self.receiver, "logistics:task-receipt", {"task_id": task.pk},
                                        {"accepted_quantity": "20.000"}), 200)
        self.assertEqual(Donation.objects.get(pk=donation_id).status, "COMPLETED")

    def test_volunteer_delivery_action_does_not_complete_donation(self):
        # Seed an assigned pickup to isolate delivery from earlier URL failures.
        donation, allocation = self.make_allocation(mode="VOLUNTEER_DELIVERY")
        task = VolunteerTask.objects.get(donation=donation)
        task.assigned_volunteer = self.volunteer
        task.status = "PICKED_UP"
        task.save()
        donation.status = "PICKED_UP"
        donation.save(update_fields=["status"])
        from django.utils import timezone
        HandoverRecord.objects.create(donation=donation, donation_request=allocation,
            revision=allocation.requested_revision, confirmed_by=self.volunteer,
            actual_quantity="20.000", unit="PORTION", handed_over_at=timezone.now())
        response = self.post_as(self.volunteer, "logistics:task-delivery", {"task_id": task.pk},
                                {"actual_quantity": "20.000"})
        self.assert_status(response, 200)
        donation.refresh_from_db()
        self.assertEqual(donation.status, "DELIVERED")
        self.assertFalse(ReceiptConfirmation.objects.filter(donation=donation).exists())

    def test_receipt_totals_keep_units_separate(self):
        from django.utils import timezone
        for unit, quantity in (("KG", "5.000"), ("LITRE", "7.000"), ("PORTION", "18.000")):
            receiver = self.make_receiver(quantity="20.000", unit=unit)
            donation, request = self.make_allocation(receiver=receiver, unit=unit)
            handover = HandoverRecord.objects.create(donation=donation, donation_request=request,
                revision=request.requested_revision, confirmed_by=self.donor,
                actual_quantity="20.000", unit=unit, handed_over_at=timezone.now())
            ReceiptConfirmation.objects.create(donation=donation, donation_request=request,
                handover=handover, confirmed_by=receiver, accepted_quantity=quantity,
                unit=unit, received_at=timezone.now())
            donation.status = "COMPLETED"
            donation.save(update_fields=["status"])
        response = api_for(self.donor).get("/api/analytics/")
        self.assert_status(response, 200)
        self.assertEqual({x["unit"]: Decimal(x["quantity"]) for x in response.data["quantity_redistributed"]},
                         {"KG": Decimal("5"), "LITRE": Decimal("7"), "PORTION": Decimal("18")})
