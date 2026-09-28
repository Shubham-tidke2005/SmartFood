import csv
import json

from collections import Counter
from pathlib import Path

from django.db import transaction
from django.utils import timezone

from apps.donations.models import (
    Donation,
    DonationRequest,
    DonationStatusHistory,
)

from .models import (
    MatchTrainingRecord,
    RecommendationEvaluation,
)


RESOLVED_DONATION_STATUSES = {
    Donation.Status.COMPLETED,
    Donation.Status.FAILED,
    Donation.Status.CANCELLED,
    Donation.Status.EXPIRED,
}

SELECTED_REQUEST_STATUSES = {
    DonationRequest.Status.APPROVED,
    DonationRequest.Status.CANCELLED,
}

MODEL_FEATURE_NAMES = [
    "distance",
    "quantity_match",
    "availability_overlap",
    "transport_readiness",
]


def find_recommendation_evaluation(
    donation_request,
):
    """
    Find the latest eligible recommendation evaluation that
    existed before the receiver was approved.

    This prevents using a recommendation generated after the
    approval decision.
    """
    if donation_request.decided_at is None:
        return None

    return (
        RecommendationEvaluation.objects
        .select_related(
            "run",
            "receiver",
        )
        .filter(
            run__donation=(
                donation_request.donation
            ),
            run__revision=(
                donation_request
                .requested_revision
            ),
            receiver=(
                donation_request.receiver
            ),
            eligible=True,
            run__created_at__lte=(
                donation_request.decided_at
            ),
        )
        .order_by("-run__created_at")
        .first()
    )


def find_terminal_history(donation):
    return (
        DonationStatusHistory.objects
        .filter(
            donation=donation,
            to_status__in=(
                RESOLVED_DONATION_STATUSES
            ),
        )
        .order_by("-created_at")
        .first()
    )


def validate_feature_snapshot(snapshot):
    normalized_features = snapshot.get(
        "normalized_features"
    )

    if not isinstance(
        normalized_features,
        dict,
    ):
        return False

    return all(
        feature_name in normalized_features
        for feature_name in MODEL_FEATURE_NAMES
    )


def determine_failure_reason(
    *,
    donation_request,
    terminal_history,
):
    if (
        donation_request.donation.status
        == Donation.Status.COMPLETED
    ):
        return ""

    if (
        terminal_history
        and terminal_history.reason
    ):
        return terminal_history.reason.strip()

    if donation_request.reason:
        return donation_request.reason.strip()

    return (
        "Resolved without a recorded failure reason."
    )


@transaction.atomic
def collect_training_records(
    *,
    dataset_source,
):
    """
    Collect training examples from resolved selected matches.

    Important:
    - Unselected recommendation candidates are ignored.
    - Rejected requests are ignored.
    - Pending or unresolved transactions are ignored.
    - Features come from recommendation-time snapshots.
    """
    valid_sources = {
        choice
        for choice, _label
        in MatchTrainingRecord
        .DatasetSource.choices
    }

    if dataset_source not in valid_sources:
        raise ValueError(
            "Invalid dataset source. Choose one of: "
            + ", ".join(
                sorted(valid_sources)
            )
        )

    requests = (
        DonationRequest.objects
        .select_related(
            "donation",
            "receiver",
            "requested_revision",
        )
        .filter(
            status__in=(
                SELECTED_REQUEST_STATUSES
            ),
            decided_at__isnull=False,
            donation__status__in=(
                RESOLVED_DONATION_STATUSES
            ),
        )
        .order_by("decided_at")
    )

    statistics = {
        "examined": 0,
        "created": 0,
        "already_exists": 0,
        "missing_recommendation_snapshot": 0,
        "invalid_feature_snapshot": 0,
        "missing_outcome_timestamp": 0,
        "outcome_before_approval": 0,
        "source_conflict": 0,
    }

    for donation_request in requests:
        statistics["examined"] += 1

        existing = (
            MatchTrainingRecord.objects
            .filter(
                donation_request=(
                    donation_request
                )
            )
            .first()
        )

        if existing is not None:
            if (
                existing.dataset_source
                != dataset_source
            ):
                statistics[
                    "source_conflict"
                ] += 1
            else:
                statistics[
                    "already_exists"
                ] += 1

            continue

        evaluation = (
            find_recommendation_evaluation(
                donation_request
            )
        )

        if evaluation is None:
            statistics[
                "missing_recommendation_snapshot"
            ] += 1
            continue

        feature_snapshot = (
            evaluation.feature_snapshot
        )

        if not validate_feature_snapshot(
            feature_snapshot
        ):
            statistics[
                "invalid_feature_snapshot"
            ] += 1
            continue

        terminal_history = (
            find_terminal_history(
                donation_request.donation
            )
        )

        outcome_at = None

        if terminal_history is not None:
            outcome_at = (
                terminal_history.created_at
            )
        elif (
            donation_request
            .donation
            .closed_at
            is not None
        ):
            outcome_at = (
                donation_request
                .donation
                .closed_at
            )

        if outcome_at is None:
            statistics[
                "missing_outcome_timestamp"
            ] += 1
            continue

        if (
            outcome_at
            < donation_request.decided_at
        ):
            statistics[
                "outcome_before_approval"
            ] += 1
            continue

        target_completed = (
            donation_request.donation.status
            == Donation.Status.COMPLETED
        )

        failure_reason = (
            determine_failure_reason(
                donation_request=(
                    donation_request
                ),
                terminal_history=(
                    terminal_history
                ),
            )
        )

        MatchTrainingRecord.objects.create(
            donation_request=(
                donation_request
            ),
            recommendation_evaluation=(
                evaluation
            ),
            dataset_source=dataset_source,
            target_completed=(
                target_completed
            ),
            approved_at=(
                donation_request.decided_at
            ),
            outcome_at=outcome_at,
            failure_reason=failure_reason,
            feature_snapshot=(
                feature_snapshot
            ),
            baseline_version=(
                evaluation.run.model_version
            ),
            baseline_score=(
                evaluation.baseline_score
            ),
            recommendation_timestamp=(
                evaluation.run.created_at
            ),
        )

        statistics["created"] += 1

    return statistics


def flatten_training_record(record):
    snapshot = record.feature_snapshot

    normalized = snapshot.get(
        "normalized_features",
        {},
    )

    donation_request = (
        record.donation_request
    )

    return {
        "training_record_id": str(record.id),
        "donation_request_id": str(
            donation_request.id
        ),
        "donation_id": str(
            donation_request.donation_id
        ),
        "receiver_id": str(
            donation_request.receiver_id
        ),
        "requested_revision_id": str(
            donation_request
            .requested_revision_id
        ),
        "recommendation_evaluation_id": str(
            record.recommendation_evaluation_id
        ),
        "dataset_source": (
            record.dataset_source
        ),
        "recommendation_timestamp": (
            record
            .recommendation_timestamp
            .isoformat()
        ),
        "approved_at": (
            record.approved_at.isoformat()
        ),
        "outcome_at": (
            record.outcome_at.isoformat()
        ),
        "category_id": snapshot.get(
            "category_id"
        ),
        "category_name": snapshot.get(
            "category_name"
        ),
        "unit": snapshot.get("unit"),
        "donation_quantity": snapshot.get(
            "donation_quantity"
        ),
        "remaining_capacity": snapshot.get(
            "remaining_capacity"
        ),
        "approximate_distance_km": (
            snapshot.get(
                "approximate_distance_km"
            )
        ),
        "maximum_service_distance_km": (
            snapshot.get(
                "maximum_service_distance_km"
            )
        ),
        "active_allocations": snapshot.get(
            "active_allocations"
        ),
        "maximum_active_allocations": (
            snapshot.get(
                "maximum_active_allocations"
            )
        ),
        "distance": normalized.get(
            "distance"
        ),
        "quantity_match": normalized.get(
            "quantity_match"
        ),
        "availability_overlap": (
            normalized.get(
                "availability_overlap"
            )
        ),
        "transport_readiness": (
            normalized.get(
                "transport_readiness"
            )
        ),
        "baseline_version": (
            record.baseline_version
        ),
        "baseline_score": (
            str(record.baseline_score)
            if record.baseline_score
            is not None
            else ""
        ),
        "target_completed": (
            1
            if record.target_completed
            else 0
        ),
        "failure_reason": (
            record.failure_reason
        ),
    }


CSV_FIELD_NAMES = [
    "training_record_id",
    "donation_request_id",
    "donation_id",
    "receiver_id",
    "requested_revision_id",
    "recommendation_evaluation_id",
    "dataset_source",
    "recommendation_timestamp",
    "approved_at",
    "outcome_at",
    "category_id",
    "category_name",
    "unit",
    "donation_quantity",
    "remaining_capacity",
    "approximate_distance_km",
    "maximum_service_distance_km",
    "active_allocations",
    "maximum_active_allocations",
    "distance",
    "quantity_match",
    "availability_overlap",
    "transport_readiness",
    "baseline_version",
    "baseline_score",
    "target_completed",
    "failure_reason",
]


def build_dataset_metadata(records):
    source_counts = Counter(
        record.dataset_source
        for record in records
    )

    target_counts = Counter(
        (
            "completed"
            if record.target_completed
            else "not_completed"
        )
        for record in records
    )

    return {
        "dataset_name": (
            "SmartFood Match Completion Dataset"
        ),
        "dataset_version": "1.0",
        "generated_at": (
            timezone.now().isoformat()
        ),
        "row_count": len(records),
        "prediction_target": {
            "name": "target_completed",
            "definition": (
                "Whether an approved donation-receiver "
                "match reached receiver-confirmed "
                "COMPLETED status."
            ),
            "positive_value": 1,
            "negative_value": 0,
        },
        "inclusion_rules": [
            (
                "The receiver request was selected and "
                "approved."
            ),
            (
                "The donation reached a resolved terminal "
                "status."
            ),
            (
                "A valid recommendation-time feature "
                "snapshot exists."
            ),
        ],
        "exclusion_rules": [
            "Unselected receivers are excluded.",
            "Rejected requests are excluded.",
            "Withdrawn requests are excluded.",
            "Pending transactions are excluded.",
            (
                "Transactions without a point-in-time "
                "feature snapshot are excluded."
            ),
        ],
        "input_features": {
            "distance": (
                "Normalized proximity within the receiver's "
                "maximum service distance."
            ),
            "quantity_match": (
                "Fraction of remaining receiver need "
                "satisfied by the donation."
            ),
            "availability_overlap": (
                "Fraction of pickup window overlapping "
                "receiver availability."
            ),
            "transport_readiness": (
                "Remaining operational allocation capacity."
            ),
            "category_name": (
                "Food category available at recommendation "
                "time."
            ),
            "unit": (
                "Donation quantity unit available at "
                "recommendation time."
            ),
            "donation_quantity": (
                "Donation quantity available at "
                "recommendation time."
            ),
        },
        "non_feature_columns": [
            "training_record_id",
            "donation_request_id",
            "donation_id",
            "receiver_id",
            "requested_revision_id",
            "recommendation_evaluation_id",
            "recommendation_timestamp",
            "approved_at",
            "outcome_at",
            "baseline_version",
            "baseline_score",
            "failure_reason",
            "dataset_source",
            "target_completed",
        ],
        "leakage_warning": (
            "Approval time, outcome time, failure reason "
            "and delivery outcome must never be used as "
            "model input features."
        ),
        "source_counts": dict(source_counts),
        "target_counts": dict(target_counts),
    }


def export_training_dataset(
    *,
    csv_path,
    metadata_path,
    dataset_sources=None,
):
    queryset = (
        MatchTrainingRecord.objects
        .select_related(
            "donation_request",
            "donation_request__donation",
            "donation_request__receiver",
            "donation_request__requested_revision",
            "recommendation_evaluation",
        )
        .order_by(
            "approved_at",
            "id",
        )
    )

    if dataset_sources:
        queryset = queryset.filter(
            dataset_source__in=(
                dataset_sources
            )
        )

    records = list(queryset)

    csv_path = Path(csv_path)
    metadata_path = Path(metadata_path)

    csv_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    metadata_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with csv_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as csv_file:
        writer = csv.DictWriter(
            csv_file,
            fieldnames=CSV_FIELD_NAMES,
        )

        writer.writeheader()

        for record in records:
            writer.writerow(
                flatten_training_record(
                    record
                )
            )

    metadata = build_dataset_metadata(
        records
    )

    with metadata_path.open(
        "w",
        encoding="utf-8",
    ) as metadata_file:
        json.dump(
            metadata,
            metadata_file,
            indent=2,
            ensure_ascii=False,
        )

    return {
        "row_count": len(records),
        "csv_path": str(csv_path),
        "metadata_path": str(
            metadata_path
        ),
    }