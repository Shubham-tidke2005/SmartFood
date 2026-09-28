import argparse
import csv
import json
import math
import random
import uuid

from collections import Counter
from datetime import datetime, timedelta, timezone
from pathlib import Path


DEFAULT_ROWS = 3000
DEFAULT_SEED = 42

BASELINE_VERSION = "baseline-2.0"

BASELINE_WEIGHTS = {
    "distance": 0.30,
    "quantity_match": 0.30,
    "availability_overlap": 0.20,
    "transport_readiness": 0.20,
}

CATEGORY_UNITS = {
    "Prepared Meals": "PORTION",
    "Bakery": "PACKAGE",
    "Fruits and Vegetables": "KG",
    "Dairy Products": "LITRE",
    "Packaged Food": "PACKAGE",
    "Beverages": "LITRE",
    "Dry Food": "KG",
}

FAILURE_REASONS = {
    "distance": "COLLECTION_DISTANCE_PROBLEM",
    "quantity_match": "QUANTITY_REQUIREMENT_CHANGED",
    "availability_overlap": "MISSED_RECEIVING_WINDOW",
    "transport_readiness": "TRANSPORT_FAILURE",
}

CSV_FIELDS = [
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


def clamp(value, minimum=0.0, maximum=1.0):
    return max(
        minimum,
        min(value, maximum),
    )


def sigmoid(value):
    return 1.0 / (
        1.0 + math.exp(-value)
    )


def random_uuid():
    return str(uuid.uuid4())


def random_timestamp(
    random_generator,
    start,
    end,
):
    total_seconds = int(
        (end - start).total_seconds()
    )

    offset = random_generator.randint(
        0,
        total_seconds,
    )

    return start + timedelta(
        seconds=offset
    )


def generate_transport_readiness(
    random_generator,
):
    maximum_allocations = (
        random_generator.randint(1, 5)
    )

    active_allocations = (
        random_generator.randint(
            0,
            maximum_allocations - 1,
        )
    )

    readiness = (
        (
            maximum_allocations
            - active_allocations
        )
        / maximum_allocations
    )

    return (
        active_allocations,
        maximum_allocations,
        readiness,
    )


def calculate_baseline_score(
    *,
    distance,
    quantity_match,
    availability_overlap,
    transport_readiness,
):
    score = (
        distance
        * BASELINE_WEIGHTS["distance"]
        + quantity_match
        * BASELINE_WEIGHTS[
            "quantity_match"
        ]
        + availability_overlap
        * BASELINE_WEIGHTS[
            "availability_overlap"
        ]
        + transport_readiness
        * BASELINE_WEIGHTS[
            "transport_readiness"
        ]
    )

    return round(score * 100, 2)


def calculate_completion_probability(
    *,
    random_generator,
    distance,
    quantity_match,
    availability_overlap,
    transport_readiness,
):
    """
    Synthetic outcome mechanism.

    Random noise prevents labels from being a direct copy
    of the baseline score.
    """
    random_noise = (
        random_generator.gauss(
            0.0,
            0.55,
        )
    )

    logit = (
        -2.10
        + 1.20 * distance
        + 1.00 * quantity_match
        + 1.40 * availability_overlap
        + 1.30 * transport_readiness
        + random_noise
    )

    return clamp(
        sigmoid(logit),
        minimum=0.05,
        maximum=0.95,
    )


def choose_failure_reason(
    *,
    random_generator,
    distance,
    quantity_match,
    availability_overlap,
    transport_readiness,
):
    factors = {
        "distance": distance,
        "quantity_match": quantity_match,
        "availability_overlap": (
            availability_overlap
        ),
        "transport_readiness": (
            transport_readiness
        ),
    }

    weakest_factor = min(
        factors,
        key=factors.get,
    )

    if random_generator.random() < 0.80:
        return FAILURE_REASONS[
            weakest_factor
        ]

    return random_generator.choice([
        "RECEIVER_CANCELLED",
        "DONOR_CANCELLED",
        "FOOD_UNAVAILABLE_AT_PICKUP",
        "DELIVERY_REJECTED",
        "OPERATIONAL_FAILURE",
    ])


def generate_record(
    random_generator,
    record_number,
):
    category_name = (
        random_generator.choice(
            list(CATEGORY_UNITS.keys())
        )
    )

    unit = CATEGORY_UNITS[
        category_name
    ]

    maximum_distance = round(
        random_generator.uniform(
            5.0,
            30.0,
        ),
        2,
    )

    distance_feature = clamp(
        random_generator.betavariate(
            2.2,
            1.8,
        )
    )

    approximate_distance = round(
        maximum_distance
        * (1.0 - distance_feature),
        2,
    )

    remaining_capacity = round(
        random_generator.uniform(
            10.0,
            300.0,
        ),
        3,
    )

    quantity_match = clamp(
        random_generator.betavariate(
            2.0,
            1.7,
        )
    )

    donation_quantity = round(
        max(
            0.001,
            remaining_capacity
            * quantity_match,
        ),
        3,
    )

    availability_overlap = clamp(
        random_generator.betavariate(
            2.4,
            1.5,
        )
    )

    (
        active_allocations,
        maximum_allocations,
        transport_readiness,
    ) = generate_transport_readiness(
        random_generator
    )

    baseline_score = (
        calculate_baseline_score(
            distance=distance_feature,
            quantity_match=quantity_match,
            availability_overlap=(
                availability_overlap
            ),
            transport_readiness=(
                transport_readiness
            ),
        )
    )

    completion_probability = (
        calculate_completion_probability(
            random_generator=(
                random_generator
            ),
            distance=distance_feature,
            quantity_match=quantity_match,
            availability_overlap=(
                availability_overlap
            ),
            transport_readiness=(
                transport_readiness
            ),
        )
    )

    target_completed = int(
        random_generator.random()
        < completion_probability
    )

    failure_reason = ""

    if target_completed == 0:
        failure_reason = (
            choose_failure_reason(
                random_generator=(
                    random_generator
                ),
                distance=distance_feature,
                quantity_match=(
                    quantity_match
                ),
                availability_overlap=(
                    availability_overlap
                ),
                transport_readiness=(
                    transport_readiness
                ),
            )
        )

    dataset_start = datetime(
        2025,
        1,
        1,
        tzinfo=timezone.utc,
    )

    dataset_end = datetime(
        2026,
        9,
        1,
        tzinfo=timezone.utc,
    )

    recommendation_timestamp = (
        random_timestamp(
            random_generator,
            dataset_start,
            dataset_end,
        )
    )

    approved_at = (
        recommendation_timestamp
        + timedelta(
            minutes=random_generator.randint(
                5,
                360,
            )
        )
    )

    outcome_at = (
        approved_at
        + timedelta(
            minutes=random_generator.randint(
                30,
                1440,
            )
        )
    )

    category_code = (
        category_name
        .lower()
        .replace(" ", "-")
    )

    return {
        "training_record_id": (
            random_uuid()
        ),
        "donation_request_id": (
            random_uuid()
        ),
        "donation_id": random_uuid(),
        "receiver_id": random_uuid(),
        "requested_revision_id": (
            random_uuid()
        ),
        "recommendation_evaluation_id": (
            random_uuid()
        ),
        "dataset_source": "SYNTHETIC",
        "recommendation_timestamp": (
            recommendation_timestamp
            .isoformat()
        ),
        "approved_at": (
            approved_at.isoformat()
        ),
        "outcome_at": (
            outcome_at.isoformat()
        ),
        "category_id": category_code,
        "category_name": category_name,
        "unit": unit,
        "donation_quantity": (
            donation_quantity
        ),
        "remaining_capacity": (
            remaining_capacity
        ),
        "approximate_distance_km": (
            approximate_distance
        ),
        "maximum_service_distance_km": (
            maximum_distance
        ),
        "active_allocations": (
            active_allocations
        ),
        "maximum_active_allocations": (
            maximum_allocations
        ),
        "distance": round(
            distance_feature,
            6,
        ),
        "quantity_match": round(
            quantity_match,
            6,
        ),
        "availability_overlap": round(
            availability_overlap,
            6,
        ),
        "transport_readiness": round(
            transport_readiness,
            6,
        ),
        "baseline_version": (
            BASELINE_VERSION
        ),
        "baseline_score": baseline_score,
        "target_completed": (
            target_completed
        ),
        "failure_reason": (
            failure_reason
        ),
        "_completion_probability": round(
            completion_probability,
            6,
        ),
        "_record_number": record_number,
    }


def write_csv(records, output_path):
    output_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    with output_path.open(
        "w",
        newline="",
        encoding="utf-8",
    ) as output_file:
        writer = csv.DictWriter(
            output_file,
            fieldnames=CSV_FIELDS,
            extrasaction="ignore",
        )

        writer.writeheader()

        for record in records:
            writer.writerow(record)


def write_metadata(
    *,
    records,
    metadata_path,
    seed,
):
    metadata_path.parent.mkdir(
        parents=True,
        exist_ok=True,
    )

    target_counts = Counter(
        record["target_completed"]
        for record in records
    )

    category_counts = Counter(
        record["category_name"]
        for record in records
    )

    failure_counts = Counter(
        record["failure_reason"]
        for record in records
        if record["failure_reason"]
    )

    metadata = {
        "dataset_name": (
            "SmartFood Synthetic Match "
            "Completion Dataset"
        ),
        "dataset_version": "synthetic-1.0",
        "dataset_source": "SYNTHETIC",
        "generated_at": (
            datetime.now(
                timezone.utc
            ).isoformat()
        ),
        "random_seed": seed,
        "row_count": len(records),
        "target_definition": (
            "Whether an approved synthetic "
            "donation-receiver match reaches "
            "confirmed completion."
        ),
        "target_counts": {
            "completed": target_counts.get(
                1,
                0,
            ),
            "not_completed": (
                target_counts.get(0, 0)
            ),
        },
        "category_counts": dict(
            category_counts
        ),
        "failure_reason_counts": dict(
            failure_counts
        ),
        "baseline_version": (
            BASELINE_VERSION
        ),
        "baseline_weights": (
            BASELINE_WEIGHTS
        ),
        "model_input_features": [
            "distance",
            "quantity_match",
            "availability_overlap",
            "transport_readiness",
            "category_name",
            "unit",
            "donation_quantity",
            "remaining_capacity",
            "approximate_distance_km",
            "maximum_service_distance_km",
            "active_allocations",
            "maximum_active_allocations",
        ],
        "excluded_from_model_inputs": [
            "target_completed",
            "failure_reason",
            "approved_at",
            "outcome_at",
            "baseline_score",
            "database identifiers",
        ],
        "limitation": (
            "This dataset is synthetic and demonstrates "
            "the technical ML pipeline only. Results must "
            "not be presented as validated real-world "
            "predictive performance."
        ),
    }

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


def parse_arguments():
    parser = argparse.ArgumentParser(
        description=(
            "Generate the SmartFood synthetic "
            "match-completion dataset."
        )
    )

    parser.add_argument(
        "--rows",
        type=int,
        default=DEFAULT_ROWS,
        help=(
            "Number of synthetic records. "
            f"Default: {DEFAULT_ROWS}"
        ),
    )

    parser.add_argument(
        "--seed",
        type=int,
        default=DEFAULT_SEED,
        help=(
            "Random seed for reproducibility. "
            f"Default: {DEFAULT_SEED}"
        ),
    )

    parser.add_argument(
        "--output-directory",
        default=None,
        help=(
            "Optional output directory."
        ),
    )

    return parser.parse_args()


def main():
    arguments = parse_arguments()

    if arguments.rows < 100:
        raise ValueError(
            "Generate at least 100 rows."
        )

    script_path = Path(__file__).resolve()

    ml_directory = script_path.parent.parent

    if arguments.output_directory:
        output_directory = Path(
            arguments.output_directory
        ).resolve()
    else:
        output_directory = (
            ml_directory
            / "data"
            / "synthetic"
        )

    csv_path = (
        output_directory
        / "smartfood_synthetic_matches.csv"
    )

    metadata_path = (
        output_directory
        / "generation_metadata.json"
    )

    random_generator = random.Random(
        arguments.seed
    )

    records = [
        generate_record(
            random_generator,
            record_number,
        )
        for record_number in range(
            1,
            arguments.rows + 1,
        )
    ]

    write_csv(
        records,
        csv_path,
    )

    write_metadata(
        records=records,
        metadata_path=metadata_path,
        seed=arguments.seed,
    )

    completed_count = sum(
        record["target_completed"]
        for record in records
    )

    failed_count = (
        len(records) - completed_count
    )

    print(
        "Synthetic dataset generated successfully."
    )

    print(f"Rows: {len(records)}")
    print(
        f"Completed: {completed_count}"
    )
    print(
        f"Not completed: {failed_count}"
    )
    print(f"CSV: {csv_path}")
    print(
        f"Metadata: {metadata_path}"
    )


if __name__ == "__main__":
    main()