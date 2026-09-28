from decimal import Decimal

from django.conf import settings


DEFAULT_BASELINE_VERSION = "baseline-2.0"

DEFAULT_BASELINE_WEIGHTS = {
    "distance": Decimal("0.30"),
    "quantity_match": Decimal("0.30"),
    "availability_overlap": Decimal("0.20"),
    "transport_readiness": Decimal("0.20"),
}


def get_baseline_configuration():
    """
    Read optional overrides from Django settings.

    Example:

    SMARTFOOD_RECOMMENDATIONS = {
        "BASELINE_VERSION": "baseline-2.0",
        "BASELINE_WEIGHTS": {
            "distance": 0.30,
            "quantity_match": 0.30,
            "availability_overlap": 0.20,
            "transport_readiness": 0.20,
        },
    }
    """
    configured = getattr(
        settings,
        "SMARTFOOD_RECOMMENDATIONS",
        {},
    )

    version = configured.get(
        "BASELINE_VERSION",
        DEFAULT_BASELINE_VERSION,
    )

    configured_weights = configured.get(
        "BASELINE_WEIGHTS",
        DEFAULT_BASELINE_WEIGHTS,
    )

    required_features = {
        "distance",
        "quantity_match",
        "availability_overlap",
        "transport_readiness",
    }

    missing_features = (
        required_features
        - set(configured_weights.keys())
    )

    if missing_features:
        missing = ", ".join(
            sorted(missing_features)
        )

        raise ValueError(
            "Missing baseline weights: "
            f"{missing}."
        )

    weights = {
        name: Decimal(str(
            configured_weights[name]
        ))
        for name in required_features
    }

    if any(
        weight < 0
        for weight in weights.values()
    ):
        raise ValueError(
            "Baseline weights cannot be negative."
        )

    total_weight = sum(weights.values())

    if total_weight <= 0:
        raise ValueError(
            "At least one baseline weight must "
            "be greater than zero."
        )

    normalized_weights = {
        name: weight / total_weight
        for name, weight in weights.items()
    }

    return {
        "version": str(version),
        "weights": normalized_weights,
    }


def weights_for_json(weights):
    return {
        name: round(float(weight), 6)
        for name, weight in weights.items()
    }