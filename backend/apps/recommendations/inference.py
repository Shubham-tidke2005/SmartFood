import hashlib
import json
import logging

from copy import deepcopy
from dataclasses import dataclass
from decimal import Decimal, ROUND_HALF_UP
from pathlib import Path
from threading import Lock

from django.conf import settings

from .eligibility import count_active_allocations


logger = logging.getLogger(__name__)

SCORE_QUANTIZER = Decimal("0.01")

_model_cache = None
_model_cache_key = None
_model_lock = Lock()


class ModelInferenceError(Exception):
    """Raised when ML inference cannot be completed safely."""


@dataclass(frozen=True)
class ModelBundle:
    pipeline: object
    metadata: dict
    pipeline_path: Path
    metadata_path: Path


def calculate_sha256(file_path):
    digest = hashlib.sha256()

    with file_path.open("rb") as model_file:
        for chunk in iter(
            lambda: model_file.read(1024 * 1024),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def get_model_paths():
    configuration = getattr(
        settings,
        "SMARTFOOD_ML",
        {},
    )

    pipeline_path = Path(
        configuration.get(
            "PIPELINE_PATH",
            settings.BASE_DIR.parent
            / "ml"
            / "models"
            / "completion_pipeline.joblib",
        )
    )

    metadata_path = Path(
        configuration.get(
            "METADATA_PATH",
            settings.BASE_DIR.parent
            / "ml"
            / "models"
            / "model_metadata.json",
        )
    )

    return pipeline_path, metadata_path


def validate_metadata(metadata):
    required_fields = [
        "model_version",
        "numeric_features",
        "categorical_features",
        "artifact_sha256",
    ]

    missing_fields = [
        field_name
        for field_name in required_fields
        if not metadata.get(field_name)
    ]

    if missing_fields:
        raise ModelInferenceError(
            "Model metadata is missing required fields: "
            + ", ".join(missing_fields)
        )

    expected_features = {
        "distance",
        "quantity_match",
        "availability_overlap",
        "transport_readiness",
        "donation_quantity",
        "remaining_capacity",
        "approximate_distance_km",
        "maximum_service_distance_km",
        "active_allocations",
        "maximum_active_allocations",
        "category_name",
        "unit",
    }

    actual_features = set(
        metadata["numeric_features"]
        + metadata["categorical_features"]
    )

    missing_model_features = (
        expected_features - actual_features
    )

    if missing_model_features:
        raise ModelInferenceError(
            "The saved model does not contain all required "
            "SmartFood features: "
            + ", ".join(
                sorted(missing_model_features)
            )
        )


def load_model_bundle():
    """
    Load and cache the pipeline.

    The cache key includes file modification times, so the
    application reloads the model after the artifact changes.
    """
    global _model_cache
    global _model_cache_key

    configuration = getattr(
        settings,
        "SMARTFOOD_ML",
        {},
    )

    if not configuration.get("ENABLED", True):
        raise ModelInferenceError(
            "ML inference is disabled."
        )

    pipeline_path, metadata_path = get_model_paths()

    if not pipeline_path.is_file():
        raise ModelInferenceError(
            f"Model pipeline was not found at "
            f"{pipeline_path}."
        )

    if not metadata_path.is_file():
        raise ModelInferenceError(
            f"Model metadata was not found at "
            f"{metadata_path}."
        )

    cache_key = (
        str(pipeline_path.resolve()),
        pipeline_path.stat().st_mtime_ns,
        str(metadata_path.resolve()),
        metadata_path.stat().st_mtime_ns,
    )

    if (
        _model_cache is not None
        and _model_cache_key == cache_key
    ):
        return _model_cache

    with _model_lock:
        if (
            _model_cache is not None
            and _model_cache_key == cache_key
        ):
            return _model_cache

        try:
            import joblib
        except ImportError as error:
            raise ModelInferenceError(
                "joblib is not installed in the Django "
                "environment."
            ) from error

        try:
            with metadata_path.open(
                "r",
                encoding="utf-8",
            ) as metadata_file:
                metadata = json.load(metadata_file)
        except (OSError, json.JSONDecodeError) as error:
            raise ModelInferenceError(
                "Model metadata could not be read."
            ) from error

        validate_metadata(metadata)

        verify_hash = configuration.get(
            "VERIFY_ARTIFACT_HASH",
            True,
        )

        if verify_hash:
            actual_hash = calculate_sha256(
                pipeline_path
            )

            expected_hash = metadata[
                "artifact_sha256"
            ]

            if actual_hash != expected_hash:
                raise ModelInferenceError(
                    "The model artifact checksum does not "
                    "match its metadata."
                )

        try:
            pipeline = joblib.load(pipeline_path)
        except Exception as error:
            raise ModelInferenceError(
                "The saved model pipeline could not be "
                "loaded."
            ) from error

        if not hasattr(pipeline, "predict_proba"):
            raise ModelInferenceError(
                "The saved pipeline does not support "
                "probability prediction."
            )

        bundle = ModelBundle(
            pipeline=pipeline,
            metadata=metadata,
            pipeline_path=pipeline_path,
            metadata_path=metadata_path,
        )

        _model_cache = bundle
        _model_cache_key = cache_key

        return bundle


def clear_model_cache():
    global _model_cache
    global _model_cache_key

    with _model_lock:
        _model_cache = None
        _model_cache_key = None


def get_positive_class_index(pipeline):
    classes = getattr(
        pipeline,
        "classes_",
        None,
    )

    if classes is None:
        classifier = (
            getattr(
                pipeline,
                "named_steps",
                {},
            ).get("classifier")
        )

        classes = getattr(
            classifier,
            "classes_",
            None,
        )

    if classes is None:
        raise ModelInferenceError(
            "The model does not expose its classes."
        )

    classes = list(classes)

    for positive_value in [
        1,
        True,
        "1",
        "COMPLETED",
    ]:
        if positive_value in classes:
            return classes.index(positive_value)

    if len(classes) == 2:
        return 1

    raise ModelInferenceError(
        "The positive model class could not be identified."
    )


def build_model_row(
    *,
    candidate,
    revision,
):
    decision = candidate["decision"]
    profile = decision.profile
    receiver = candidate["receiver"]

    normalized = candidate[
        "feature_snapshot"
    ]["normalized_features"]

    active_allocations = (
        count_active_allocations(receiver)
    )

    return {
        "distance": float(
            normalized["distance"]
        ),
        "quantity_match": float(
            normalized["quantity_match"]
        ),
        "availability_overlap": float(
            normalized["availability_overlap"]
        ),
        "transport_readiness": float(
            normalized["transport_readiness"]
        ),
        "donation_quantity": float(
            revision.quantity
        ),
        "remaining_capacity": float(
            decision.requirement.remaining_quantity
        ),
        "approximate_distance_km": float(
            decision.approximate_distance_km
        ),
        "maximum_service_distance_km": float(
            profile.max_service_distance_km
        ),
        "active_allocations": (
            active_allocations
        ),
        "maximum_active_allocations": (
            profile.max_active_allocations
        ),
        "category_name": (
            revision.category.name
        ),
        "unit": revision.unit,
    }


def score_candidates_with_model(
    *,
    candidates,
    revision,
):
    """
    Score eligible candidates using completion probability.

    The supplied candidate dictionaries are copied. Baseline
    scores remain in each feature snapshot for comparison.
    """
    eligible_candidates = [
        candidate
        for candidate in candidates
        if candidate["eligible"]
    ]

    if not eligible_candidates:
        return {
            "candidates": candidates,
            "model_version": None,
            "model_name": None,
        }

    bundle = load_model_bundle()

    try:
        import pandas as pd
    except ImportError as error:
        raise ModelInferenceError(
            "pandas is not installed in the Django "
            "environment."
        ) from error

    rows = [
        build_model_row(
            candidate=candidate,
            revision=revision,
        )
        for candidate in eligible_candidates
    ]

    feature_order = (
        bundle.metadata["numeric_features"]
        + bundle.metadata["categorical_features"]
    )

    dataframe = pd.DataFrame(
        rows,
        columns=feature_order,
    )

    try:
        probabilities = (
            bundle.pipeline.predict_proba(
                dataframe
            )
        )

        positive_class_index = (
            get_positive_class_index(
                bundle.pipeline
            )
        )
    except Exception as error:
        raise ModelInferenceError(
            "The model could not score the eligible "
            "candidate pairs."
        ) from error

    if len(probabilities) != len(
        eligible_candidates
    ):
        raise ModelInferenceError(
            "The model returned an unexpected number "
            "of predictions."
        )

    model_version = bundle.metadata[
        "model_version"
    ]

    model_name = bundle.metadata.get(
        "model_name",
        "completion_classifier",
    )

    scored_by_receiver = {}

    for candidate, probability_row in zip(
        eligible_candidates,
        probabilities,
        strict=True,
    ):
        probability = float(
            probability_row[
                positive_class_index
            ]
        )

        if not 0 <= probability <= 1:
            raise ModelInferenceError(
                "The model returned an invalid "
                "probability."
            )

        scored_candidate = dict(candidate)

        feature_snapshot = deepcopy(
            candidate["feature_snapshot"]
        )

        probability_decimal = Decimal(
            str(probability)
        )

        score = (
            probability_decimal
            * Decimal("100")
        ).quantize(
            SCORE_QUANTIZER,
            rounding=ROUND_HALF_UP,
        )

        feature_snapshot["model"] = {
            "name": model_name,
            "version": model_version,
            "completion_probability": (
                str(
                    probability_decimal.quantize(
                        Decimal("0.000001"),
                        rounding=ROUND_HALF_UP,
                    )
                )
            ),
            "score_out_of_100": str(score),
            "dataset_source": (
                bundle.metadata.get(
                    "dataset_source",
                    [],
                )
            ),
            "experimental": True,
        }

        feature_snapshot[
            "matching_factors"
        ] = {
            "distance": str(
                candidate[
                    "feature_snapshot"
                ]["normalized_features"][
                    "distance"
                ]
            ),
            "quantity_match": str(
                candidate[
                    "feature_snapshot"
                ]["normalized_features"][
                    "quantity_match"
                ]
            ),
            "availability_overlap": str(
                candidate[
                    "feature_snapshot"
                ]["normalized_features"][
                    "availability_overlap"
                ]
            ),
            "transport_readiness": str(
                candidate[
                    "feature_snapshot"
                ]["normalized_features"][
                    "transport_readiness"
                ]
            ),
        }

        explanations = list(
            candidate["explanations"]
        )

        explanations.insert(
            0,
            (
                "The experimental completion model "
                f"estimated a {score}% probability of "
                "confirmed completion."
            ),
        )

        scored_candidate["score"] = score
        scored_candidate[
            "feature_snapshot"
        ] = feature_snapshot
        scored_candidate[
            "explanations"
        ] = explanations

        scored_by_receiver[
            candidate["receiver"].id
        ] = scored_candidate

    scored_candidates = []

    for candidate in candidates:
        scored_candidates.append(
            scored_by_receiver.get(
                candidate["receiver"].id,
                candidate,
            )
        )

    return {
        "candidates": scored_candidates,
        "model_version": model_version,
        "model_name": model_name,
    }