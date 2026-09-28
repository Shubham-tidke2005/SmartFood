import logging

from decimal import Decimal, ROUND_HALF_UP

from django.db import transaction
from django.utils import timezone

from apps.donations.models import Donation

from .config import (
    get_baseline_configuration,
    weights_for_json,
)
from .features import (
    build_baseline_features,
    build_considered_feature_snapshot,
    get_all_candidate_decisions,
)
from .inference import (
    ModelInferenceError,
    score_candidates_with_model,
)
from .models import (
    RecommendationCandidate,
    RecommendationEvaluation,
    RecommendationRun,
)


logger = logging.getLogger(__name__)

SCORE_QUANTIZER = Decimal("0.01")


def calculate_baseline_score(
    *,
    normalized_features,
    weights,
):
    weighted_score = sum(
        normalized_features[feature_name]
        * weights[feature_name]
        for feature_name in weights
    )

    return (
        weighted_score
        * Decimal("100")
    ).quantize(
        SCORE_QUANTIZER,
        rounding=ROUND_HALF_UP,
    )


def build_explanations(
    *,
    decision,
    revision,
    feature_snapshot,
):
    normalized = feature_snapshot[
        "normalized_features"
    ]

    distance = (
        decision.approximate_distance_km
    )

    requirement = decision.requirement

    explanations = [
        (
            f"Accepts the "
            f"{revision.category.name} category."
        ),
        (
            f"Has "
            f"{requirement.remaining_quantity} "
            f"{revision.unit} remaining capacity."
        ),
        (
            f"Approximately {distance} km away "
            f"by straight-line distance."
        ),
        (
            "Availability overlaps "
            f"{normalized['availability_overlap'] * 100:.1f}% "
            "of the pickup window."
        ),
        (
            "Transport readiness is "
            f"{normalized['transport_readiness'] * 100:.1f}% "
            "based on active allocation capacity."
        ),
        (
            "The donation satisfies approximately "
            f"{normalized['quantity_match'] * 100:.1f}% "
            "of the receiver's remaining requirement."
        ),
    ]

    return explanations


def prepare_scored_candidates(
    *,
    decisions,
    revision,
    weights,
):
    prepared = []

    for decision in decisions:
        receiver = decision.profile.user

        if not decision.eligible:
            prepared.append(
                {
                    "receiver": receiver,
                    "decision": decision,
                    "eligible": False,
                    "score": None,
                    "baseline_score": None,
                    "feature_snapshot": (
                        build_considered_feature_snapshot(
                            decision=decision,
                            revision=revision,
                        )
                    ),
                    "explanations": [],
                }
            )

            continue

        (
            normalized_features,
            feature_snapshot,
        ) = build_baseline_features(
            decision=decision,
            revision=revision,
        )

        baseline_score = (
            calculate_baseline_score(
                normalized_features=(
                    normalized_features
                ),
                weights=weights,
            )
        )

        feature_snapshot[
            "baseline_score"
        ] = str(baseline_score)

        prepared.append(
            {
                "receiver": receiver,
                "decision": decision,
                "eligible": True,
                "score": baseline_score,
                "baseline_score": (
                    baseline_score
                ),
                "feature_snapshot": (
                    feature_snapshot
                ),
                "explanations": (
                    build_explanations(
                        decision=decision,
                        revision=revision,
                        feature_snapshot=(
                            feature_snapshot
                        ),
                    )
                ),
            }
        )

    return prepared


def try_model_scoring(
    *,
    candidates,
    revision,
    baseline_version,
):
    """
    Return ML scores when inference succeeds.

    Any model-loading or inference failure returns the
    baseline candidates instead.
    """
    eligible_exists = any(
        candidate["eligible"]
        for candidate in candidates
    )

    if not eligible_exists:
        return {
            "candidates": candidates,
            "algorithm": (
                RecommendationRun.Algorithm
                .RULE_BASED_V2
            ),
            "model_version": baseline_version,
            "fallback_error": "",
        }

    try:
        result = score_candidates_with_model(
            candidates=candidates,
            revision=revision,
        )

        return {
            "candidates": result["candidates"],
            "algorithm": (
                RecommendationRun.Algorithm
                .ML_COMPLETION_V1
            ),
            "model_version": (
                result["model_version"]
            ),
            "fallback_error": "",
        }

    except Exception as error:
        # This block intentionally protects normal platform
        # operation from missing, corrupt or incompatible
        # model artifacts.
        logger.exception(
            "ML recommendation inference failed. "
            "Using the rule-based baseline."
        )

        if isinstance(
            error,
            ModelInferenceError,
        ):
            message = str(error)
        else:
            message = (
                "Unexpected inference failure: "
                f"{type(error).__name__}"
            )

        return {
            "candidates": candidates,
            "algorithm": (
                RecommendationRun.Algorithm
                .RULE_BASED_V2
            ),
            "model_version": baseline_version,
            "fallback_error": message[:2000],
        }


@transaction.atomic
def generate_recommendations(
    *,
    donation,
    requested_by,
):
    """
    Generate receiver recommendations.

    Hard eligibility is always applied first. The ML model
    scores only eligible candidates. If ML inference fails,
    the rule-based baseline completes the recommendation run.
    """
    locked_donation = (
        Donation.objects
        .select_for_update()
        .select_related("donor")
        .get(pk=donation.pk)
    )

    if (
        locked_donation.status
        != Donation.Status.AVAILABLE
    ):
        raise ValueError(
            "Recommendations can only be generated "
            "for an available donation."
        )

    revision = (
        locked_donation.revisions
        .select_related("category")
        .filter(is_current=True)
        .first()
    )

    if revision is None:
        raise ValueError(
            "The donation has no current revision."
        )

    if (
        revision.pickup_starts_at
        >= revision.pickup_deadline
    ):
        raise ValueError(
            "The donation pickup window is invalid."
        )

    if (
        revision.pickup_deadline
        <= timezone.now()
    ):
        raise ValueError(
            "Recommendations cannot be generated "
            "after the pickup deadline."
        )

    configuration = (
        get_baseline_configuration()
    )

    weights = configuration["weights"]

    baseline_version = (
        configuration["version"]
    )

    decisions = get_all_candidate_decisions(
        donation=locked_donation,
        revision=revision,
    )

    prepared_candidates = (
        prepare_scored_candidates(
            decisions=decisions,
            revision=revision,
            weights=weights,
        )
    )

    scoring_result = try_model_scoring(
        candidates=prepared_candidates,
        revision=revision,
        baseline_version=baseline_version,
    )

    prepared_candidates = scoring_result[
        "candidates"
    ]

    eligible_candidates = [
        candidate
        for candidate in prepared_candidates
        if candidate["eligible"]
    ]

    eligible_candidates.sort(
        key=lambda candidate: (
            -candidate["score"],
            candidate[
                "decision"
            ].approximate_distance_km,
            str(candidate["receiver"].id),
        )
    )

    run = RecommendationRun.objects.create(
        donation=locked_donation,
        revision=revision,
        requested_by=requested_by,
        algorithm=scoring_result[
            "algorithm"
        ],
        model_version=scoring_result[
            "model_version"
        ],
        status=(
            RecommendationRun.Status.COMPLETED
        ),
        weights=weights_for_json(weights),
        considered_count=len(
            prepared_candidates
        ),
        eligible_count=len(
            eligible_candidates
        ),
        candidate_count=len(
            eligible_candidates
        ),
        error_message=scoring_result[
            "fallback_error"
        ],
    )

    evaluation_records = []

    for candidate in prepared_candidates:
        decision = candidate["decision"]

        evaluation_records.append(
            RecommendationEvaluation(
                run=run,
                receiver=(
                    candidate["receiver"]
                ),
                eligible=(
                    candidate["eligible"]
                ),
                rejection_reasons=list(
                    decision.rejection_reasons
                ),
                eligibility_checks=(
                    decision.checks
                ),
                feature_snapshot=(
                    candidate[
                        "feature_snapshot"
                    ]
                ),
                baseline_score=(
                    candidate[
                        "baseline_score"
                    ]
                ),
            )
        )

    RecommendationEvaluation.objects.bulk_create(
        evaluation_records
    )

    candidate_records = []

    for rank, candidate in enumerate(
        eligible_candidates,
        start=1,
    ):
        decision = candidate["decision"]

        candidate_records.append(
            RecommendationCandidate(
                run=run,
                receiver=(
                    candidate["receiver"]
                ),
                rank=rank,
                score=candidate["score"],
                approximate_distance_km=(
                    decision
                    .approximate_distance_km
                ),
                remaining_capacity=(
                    decision
                    .requirement
                    .remaining_quantity
                ),
                feature_snapshot=(
                    candidate[
                        "feature_snapshot"
                    ]
                ),
                explanations=(
                    candidate["explanations"]
                ),
            )
        )

    RecommendationCandidate.objects.bulk_create(
        candidate_records
    )

    return (
        RecommendationRun.objects
        .select_related(
            "donation",
            "revision",
            "requested_by",
        )
        .prefetch_related(
            "candidates__receiver",
            "evaluations__receiver",
        )
        .get(pk=run.pk)
    )