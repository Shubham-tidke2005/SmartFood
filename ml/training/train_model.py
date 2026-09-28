import argparse
import hashlib
import json
import platform
import sys

from datetime import datetime, timezone
from pathlib import Path

import joblib
import matplotlib
import numpy as np
import pandas as pd
import sklearn

matplotlib.use("Agg")

import matplotlib.pyplot as plt

from sklearn.calibration import calibration_curve
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import (
    ConfusionMatrixDisplay,
    accuracy_score,
    average_precision_score,
    brier_score_loss,
    classification_report,
    confusion_matrix,
    f1_score,
    log_loss,
    precision_score,
    recall_score,
    roc_auc_score,
)
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import (
    OneHotEncoder,
    StandardScaler,
)


MODEL_VERSION = "completion-model-1.0"
RANDOM_STATE = 42

TRAIN_FRACTION = 0.70
VALIDATION_FRACTION = 0.15
TEST_FRACTION = 0.15

TARGET_COLUMN = "target_completed"
TIMESTAMP_COLUMN = "recommendation_timestamp"
TRANSACTION_COLUMN = "donation_id"

NUMERIC_FEATURES = [
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
]

CATEGORICAL_FEATURES = [
    "category_name",
    "unit",
]

MODEL_FEATURES = (
    NUMERIC_FEATURES
    + CATEGORICAL_FEATURES
)

FORBIDDEN_MODEL_FEATURES = {
    "target_completed",
    "failure_reason",
    "approved_at",
    "outcome_at",
    "baseline_score",
    "training_record_id",
    "donation_request_id",
    "donation_id",
    "receiver_id",
    "requested_revision_id",
    "recommendation_evaluation_id",
    "dataset_source",
    "recommendation_timestamp",
}

BASELINE_THRESHOLD = 0.50


def parse_arguments():
    script_path = Path(__file__).resolve()
    ml_directory = script_path.parent.parent

    default_dataset = (
        ml_directory
        / "data"
        / "synthetic"
        / "smartfood_synthetic_matches.csv"
    )

    default_model_directory = (
        ml_directory / "models"
    )

    default_evaluation_directory = (
        ml_directory / "evaluation"
    )

    parser = argparse.ArgumentParser(
        description=(
            "Train and evaluate SmartFood match "
            "completion classifiers."
        )
    )

    parser.add_argument(
        "--dataset",
        default=str(default_dataset),
        help="Path to the training CSV.",
    )

    parser.add_argument(
        "--model-directory",
        default=str(
            default_model_directory
        ),
        help=(
            "Directory for the saved pipeline "
            "and model metadata."
        ),
    )

    parser.add_argument(
        "--evaluation-directory",
        default=str(
            default_evaluation_directory
        ),
        help=(
            "Directory for reports, predictions "
            "and plots."
        ),
    )

    return parser.parse_args()


def validate_dataset(dataframe):
    required_columns = set(
        MODEL_FEATURES
        + [
            TARGET_COLUMN,
            TIMESTAMP_COLUMN,
            TRANSACTION_COLUMN,
            "baseline_score",
            "dataset_source",
        ]
    )

    missing_columns = (
        required_columns
        - set(dataframe.columns)
    )

    if missing_columns:
        missing = ", ".join(
            sorted(missing_columns)
        )

        raise ValueError(
            "Dataset is missing required columns: "
            f"{missing}"
        )

    accidental_features = (
        set(MODEL_FEATURES)
        & FORBIDDEN_MODEL_FEATURES
    )

    if accidental_features:
        raise ValueError(
            "Forbidden columns were configured as "
            "model inputs: "
            + ", ".join(
                sorted(accidental_features)
            )
        )

    if len(dataframe) < 100:
        raise ValueError(
            "At least 100 resolved records are required."
        )

    target_values = set(
        dataframe[TARGET_COLUMN]
        .dropna()
        .astype(int)
        .unique()
        .tolist()
    )

    if target_values != {0, 1}:
        raise ValueError(
            "The target must contain both classes 0 and 1."
        )

    if dataframe[
        TRANSACTION_COLUMN
    ].isna().any():
        raise ValueError(
            "Every row must have a donation_id."
        )

    if dataframe[
        TIMESTAMP_COLUMN
    ].isna().any():
        raise ValueError(
            "Every row must have a recommendation timestamp."
        )


def load_dataset(dataset_path):
    dataset_path = Path(
        dataset_path
    ).resolve()

    if not dataset_path.exists():
        raise FileNotFoundError(
            f"Dataset not found: {dataset_path}"
        )

    dataframe = pd.read_csv(
        dataset_path
    )

    dataframe[
        TIMESTAMP_COLUMN
    ] = pd.to_datetime(
        dataframe[TIMESTAMP_COLUMN],
        utc=True,
        errors="coerce",
    )

    dataframe[
        TARGET_COLUMN
    ] = pd.to_numeric(
        dataframe[TARGET_COLUMN],
        errors="coerce",
    )

    dataframe[
        "baseline_score"
    ] = pd.to_numeric(
        dataframe["baseline_score"],
        errors="coerce",
    )

    for column in NUMERIC_FEATURES:
        dataframe[column] = (
            pd.to_numeric(
                dataframe[column],
                errors="coerce",
            )
        )

    for column in CATEGORICAL_FEATURES:
        dataframe[column] = (
            dataframe[column]
            .astype("string")
        )

    dataframe = dataframe.dropna(
        subset=[
            TARGET_COLUMN,
            TIMESTAMP_COLUMN,
            TRANSACTION_COLUMN,
        ]
    ).copy()

    dataframe[
        TARGET_COLUMN
    ] = dataframe[
        TARGET_COLUMN
    ].astype(int)

    validate_dataset(dataframe)

    return dataframe, dataset_path


def chronological_transaction_split(
    dataframe,
):
    """
    Split transactions chronologically.

    All rows belonging to one donation remain in the same
    split, preventing transaction leakage.
    """
    transaction_times = (
        dataframe
        .groupby(
            TRANSACTION_COLUMN,
            as_index=False,
        )[TIMESTAMP_COLUMN]
        .min()
        .sort_values(
            TIMESTAMP_COLUMN,
            kind="stable",
        )
        .reset_index(drop=True)
    )

    transaction_count = len(
        transaction_times
    )

    if transaction_count < 20:
        raise ValueError(
            "At least 20 unique transactions are required "
            "for train, validation and test splitting."
        )

    train_end = int(
        transaction_count
        * TRAIN_FRACTION
    )

    validation_end = int(
        transaction_count
        * (
            TRAIN_FRACTION
            + VALIDATION_FRACTION
        )
    )

    train_end = max(train_end, 1)

    validation_end = max(
        validation_end,
        train_end + 1,
    )

    validation_end = min(
        validation_end,
        transaction_count - 1,
    )

    train_transactions = set(
        transaction_times.iloc[
            :train_end
        ][TRANSACTION_COLUMN]
    )

    validation_transactions = set(
        transaction_times.iloc[
            train_end:validation_end
        ][TRANSACTION_COLUMN]
    )

    test_transactions = set(
        transaction_times.iloc[
            validation_end:
        ][TRANSACTION_COLUMN]
    )

    if (
        train_transactions
        & validation_transactions
    ):
        raise RuntimeError(
            "Transaction leakage between train and validation."
        )

    if train_transactions & test_transactions:
        raise RuntimeError(
            "Transaction leakage between train and test."
        )

    if (
        validation_transactions
        & test_transactions
    ):
        raise RuntimeError(
            "Transaction leakage between validation and test."
        )

    train_data = dataframe[
        dataframe[
            TRANSACTION_COLUMN
        ].isin(train_transactions)
    ].copy()

    validation_data = dataframe[
        dataframe[
            TRANSACTION_COLUMN
        ].isin(validation_transactions)
    ].copy()

    test_data = dataframe[
        dataframe[
            TRANSACTION_COLUMN
        ].isin(test_transactions)
    ].copy()

    train_data = train_data.sort_values(
        TIMESTAMP_COLUMN
    )

    validation_data = (
        validation_data.sort_values(
            TIMESTAMP_COLUMN
        )
    )

    test_data = test_data.sort_values(
        TIMESTAMP_COLUMN
    )

    for split_name, split_data in [
        ("train", train_data),
        ("validation", validation_data),
        ("test", test_data),
    ]:
        classes = set(
            split_data[
                TARGET_COLUMN
            ].unique()
        )

        if classes != {0, 1}:
            raise ValueError(
                f"The {split_name} split does not "
                "contain both target classes."
            )

    return (
        train_data,
        validation_data,
        test_data,
    )


def make_preprocessor():
    numeric_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy="median",
                ),
            ),
            (
                "scaler",
                StandardScaler(),
            ),
        ]
    )

    categorical_pipeline = Pipeline(
        steps=[
            (
                "imputer",
                SimpleImputer(
                    strategy=(
                        "most_frequent"
                    ),
                ),
            ),
            (
                "one_hot",
                OneHotEncoder(
                    handle_unknown="ignore",
                ),
            ),
        ]
    )

    return ColumnTransformer(
        transformers=[
            (
                "numeric",
                numeric_pipeline,
                NUMERIC_FEATURES,
            ),
            (
                "categorical",
                categorical_pipeline,
                CATEGORICAL_FEATURES,
            ),
        ],
        remainder="drop",
    )


def build_model_candidates():
    return {
        "logistic_regression": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(),
                ),
                (
                    "classifier",
                    LogisticRegression(
                        max_iter=2000,
                        random_state=(
                            RANDOM_STATE
                        ),
                    ),
                ),
            ]
        ),
        "random_forest": Pipeline(
            steps=[
                (
                    "preprocessor",
                    make_preprocessor(),
                ),
                (
                    "classifier",
                    RandomForestClassifier(
                        n_estimators=350,
                        max_depth=12,
                        min_samples_leaf=4,
                        class_weight=(
                            "balanced_subsample"
                        ),
                        random_state=(
                            RANDOM_STATE
                        ),
                        n_jobs=-1,
                    ),
                ),
            ]
        ),
    }


def safe_roc_auc(
    targets,
    probabilities,
):
    if len(np.unique(targets)) < 2:
        return None

    return float(
        roc_auc_score(
            targets,
            probabilities,
        )
    )


def safe_average_precision(
    targets,
    probabilities,
):
    if len(np.unique(targets)) < 2:
        return None

    return float(
        average_precision_score(
            targets,
            probabilities,
        )
    )


def calculate_metrics(
    *,
    targets,
    predictions,
    probabilities,
):
    probabilities = np.clip(
        probabilities,
        1e-7,
        1 - 1e-7,
    )

    return {
        "accuracy": float(
            accuracy_score(
                targets,
                predictions,
            )
        ),
        "precision": float(
            precision_score(
                targets,
                predictions,
                zero_division=0,
            )
        ),
        "recall": float(
            recall_score(
                targets,
                predictions,
                zero_division=0,
            )
        ),
        "f1": float(
            f1_score(
                targets,
                predictions,
                zero_division=0,
            )
        ),
        "roc_auc": safe_roc_auc(
            targets,
            probabilities,
        ),
        "average_precision": (
            safe_average_precision(
                targets,
                probabilities,
            )
        ),
        "brier_score": float(
            brier_score_loss(
                targets,
                probabilities,
            )
        ),
        "log_loss": float(
            log_loss(
                targets,
                probabilities,
                labels=[0, 1],
            )
        ),
        "confusion_matrix": (
            confusion_matrix(
                targets,
                predictions,
                labels=[0, 1],
            ).tolist()
        ),
        "classification_report": (
            classification_report(
                targets,
                predictions,
                labels=[0, 1],
                target_names=[
                    "not_completed",
                    "completed",
                ],
                zero_division=0,
                output_dict=True,
            )
        ),
    }


def evaluate_pipeline(
    *,
    pipeline,
    dataframe,
):
    features = dataframe[
        MODEL_FEATURES
    ]

    targets = dataframe[
        TARGET_COLUMN
    ].to_numpy()

    probabilities = (
        pipeline.predict_proba(
            features
        )[:, 1]
    )

    predictions = (
        probabilities >= 0.50
    ).astype(int)

    metrics = calculate_metrics(
        targets=targets,
        predictions=predictions,
        probabilities=probabilities,
    )

    return (
        metrics,
        probabilities,
        predictions,
    )


def evaluate_baseline(dataframe):
    valid_data = dataframe.dropna(
        subset=["baseline_score"]
    ).copy()

    if valid_data.empty:
        return None, None, None, None

    probabilities = np.clip(
        (
            valid_data[
                "baseline_score"
            ].to_numpy(
                dtype=float
            )
            / 100.0
        ),
        0.0,
        1.0,
    )

    targets = valid_data[
        TARGET_COLUMN
    ].to_numpy()

    predictions = (
        probabilities
        >= BASELINE_THRESHOLD
    ).astype(int)

    metrics = calculate_metrics(
        targets=targets,
        predictions=predictions,
        probabilities=probabilities,
    )

    return (
        metrics,
        probabilities,
        predictions,
        valid_data,
    )


def split_summary(dataframe):
    target_counts = (
        dataframe[
            TARGET_COLUMN
        ]
        .value_counts()
        .sort_index()
        .to_dict()
    )

    return {
        "rows": int(len(dataframe)),
        "unique_transactions": int(
            dataframe[
                TRANSACTION_COLUMN
            ].nunique()
        ),
        "not_completed": int(
            target_counts.get(0, 0)
        ),
        "completed": int(
            target_counts.get(1, 0)
        ),
        "completion_rate": float(
            dataframe[
                TARGET_COLUMN
            ].mean()
        ),
        "start_timestamp": (
            dataframe[
                TIMESTAMP_COLUMN
            ].min().isoformat()
        ),
        "end_timestamp": (
            dataframe[
                TIMESTAMP_COLUMN
            ].max().isoformat()
        ),
    }


def choose_best_model(validation_results):
    """
    Select lower Brier score first because predicted
    probabilities will be used for recommendation ranking.

    F1 is used as the secondary criterion.
    """
    return min(
        validation_results,
        key=lambda model_name: (
            validation_results[
                model_name
            ]["brier_score"],
            -validation_results[
                model_name
            ]["f1"],
        ),
    )


def save_confusion_matrix(
    *,
    targets,
    predictions,
    model_name,
    output_path,
):
    figure, axis = plt.subplots(
        figsize=(6, 5)
    )

    display = ConfusionMatrixDisplay(
        confusion_matrix=(
            confusion_matrix(
                targets,
                predictions,
                labels=[0, 1],
            )
        ),
        display_labels=[
            "Not completed",
            "Completed",
        ],
    )

    display.plot(
        ax=axis,
        cmap="Blues",
        colorbar=False,
    )

    axis.set_title(
        f"SmartFood — {model_name}"
    )

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(figure)


def save_calibration_plot(
    *,
    model_probabilities,
    baseline_probabilities,
    targets,
    baseline_targets,
    model_name,
    output_path,
):
    model_true, model_predicted = (
        calibration_curve(
            targets,
            model_probabilities,
            n_bins=10,
            strategy="quantile",
        )
    )

    figure, axis = plt.subplots(
        figsize=(7, 6)
    )

    axis.plot(
        [0, 1],
        [0, 1],
        linestyle="--",
        color="black",
        label="Perfect calibration",
    )

    axis.plot(
        model_predicted,
        model_true,
        marker="o",
        linewidth=2,
        label=model_name,
    )

    if (
        baseline_probabilities
        is not None
        and baseline_targets
        is not None
    ):
        baseline_true, baseline_predicted = (
            calibration_curve(
                baseline_targets,
                baseline_probabilities,
                n_bins=10,
                strategy="quantile",
            )
        )

        axis.plot(
            baseline_predicted,
            baseline_true,
            marker="s",
            linewidth=2,
            label="Rule-based baseline",
        )

    axis.set_xlabel(
        "Predicted completion probability"
    )

    axis.set_ylabel(
        "Observed completion rate"
    )

    axis.set_title(
        "Completion probability calibration"
    )

    axis.set_xlim(0, 1)
    axis.set_ylim(0, 1)
    axis.grid(alpha=0.25)
    axis.legend()

    figure.tight_layout()

    figure.savefig(
        output_path,
        dpi=180,
        bbox_inches="tight",
    )

    plt.close(figure)


def file_sha256(file_path):
    digest = hashlib.sha256()

    with Path(file_path).open(
        "rb"
    ) as input_file:
        for chunk in iter(
            lambda: input_file.read(
                1024 * 1024
            ),
            b"",
        ):
            digest.update(chunk)

    return digest.hexdigest()


def json_safe(value):
    if isinstance(
        value,
        (np.integer,),
    ):
        return int(value)

    if isinstance(
        value,
        (np.floating,),
    ):
        return float(value)

    if isinstance(value, np.ndarray):
        return value.tolist()

    raise TypeError(
        f"Cannot JSON serialize {type(value)}"
    )


def write_json(
    path,
    content,
):
    with Path(path).open(
        "w",
        encoding="utf-8",
    ) as output_file:
        json.dump(
            content,
            output_file,
            indent=2,
            ensure_ascii=False,
            default=json_safe,
        )


def write_markdown_report(
    *,
    report,
    output_path,
):
    selected_model = report[
        "selected_model"
    ]

    selected_metrics = report[
        "test_results"
    ][selected_model]

    baseline_metrics = report[
        "test_results"
    ].get(
        "rule_based_baseline"
    )

    lines = [
        "# SmartFood Model Evaluation Report",
        "",
        f"- Model version: `{report['model_version']}`",
        (
            "- Dataset source: "
            f"`{', '.join(report['dataset_sources'])}`"
        ),
        (
            "- Selected model: "
            f"`{selected_model}`"
        ),
        (
            "- Selection rule: lowest validation "
            "Brier score, then highest validation F1"
        ),
        "",
        "## Dataset split",
        "",
        "| Split | Rows | Completed | Not completed |",
        "|---|---:|---:|---:|",
    ]

    for split_name in [
        "train",
        "validation",
        "test",
    ]:
        split = report[
            "dataset_splits"
        ][split_name]

        lines.append(
            f"| {split_name.title()} "
            f"| {split['rows']} "
            f"| {split['completed']} "
            f"| {split['not_completed']} |"
        )

    lines.extend([
        "",
        "## Selected model test metrics",
        "",
        "| Metric | Value |",
        "|---|---:|",
        (
            "| Accuracy | "
            f"{selected_metrics['accuracy']:.4f} |"
        ),
        (
            "| Precision | "
            f"{selected_metrics['precision']:.4f} |"
        ),
        (
            "| Recall | "
            f"{selected_metrics['recall']:.4f} |"
        ),
        (
            "| F1 | "
            f"{selected_metrics['f1']:.4f} |"
        ),
        (
            "| ROC-AUC | "
            f"{selected_metrics['roc_auc']:.4f} |"
        ),
        (
            "| Average precision | "
            f"{selected_metrics['average_precision']:.4f} |"
        ),
        (
            "| Brier score | "
            f"{selected_metrics['brier_score']:.4f} |"
        ),
        (
            "| Log loss | "
            f"{selected_metrics['log_loss']:.4f} |"
        ),
    ])

    if baseline_metrics:
        lines.extend([
            "",
            "## Rule-based baseline test metrics",
            "",
            "| Metric | Value |",
            "|---|---:|",
            (
                "| Accuracy | "
                f"{baseline_metrics['accuracy']:.4f} |"
            ),
            (
                "| Precision | "
                f"{baseline_metrics['precision']:.4f} |"
            ),
            (
                "| Recall | "
                f"{baseline_metrics['recall']:.4f} |"
            ),
            (
                "| F1 | "
                f"{baseline_metrics['f1']:.4f} |"
            ),
            (
                "| ROC-AUC | "
                f"{baseline_metrics['roc_auc']:.4f} |"
            ),
            (
                "| Brier score | "
                f"{baseline_metrics['brier_score']:.4f} |"
            ),
            (
                "| Log loss | "
                f"{baseline_metrics['log_loss']:.4f} |"
            ),
        ])

    lines.extend([
        "",
        "## Interpretation",
        "",
        (
            "The model estimates the probability that an "
            "eligible and approved donation-receiver match "
            "will reach confirmed completion."
        ),
        "",
        (
            "Eligibility remains controlled by Django "
            "business rules. A high model probability cannot "
            "make an ineligible receiver eligible."
        ),
        "",
        "## Limitation",
        "",
        (
            "The current evaluation uses synthetic data. "
            "It demonstrates technical feasibility and must "
            "not be presented as validated real-world "
            "predictive performance."
        ),
        "",
    ])

    Path(output_path).write_text(
        "\n".join(lines),
        encoding="utf-8",
    )


def save_test_predictions(
    *,
    test_data,
    selected_model_name,
    model_probabilities,
    model_predictions,
    baseline_probabilities,
    output_path,
):
    predictions = pd.DataFrame({
        "donation_id": (
            test_data[
                TRANSACTION_COLUMN
            ].astype(str).to_numpy()
        ),
        "recommendation_timestamp": (
            test_data[
                TIMESTAMP_COLUMN
            ].astype(str).to_numpy()
        ),
        "actual_completed": (
            test_data[
                TARGET_COLUMN
            ].to_numpy()
        ),
        "model_name": (
            selected_model_name
        ),
        "model_probability": (
            model_probabilities
        ),
        "model_prediction": (
            model_predictions
        ),
        "baseline_probability": (
            baseline_probabilities
            if baseline_probabilities
            is not None
            else np.nan
        ),
    })

    predictions.to_csv(
        output_path,
        index=False,
    )


def main():
    arguments = parse_arguments()

    model_directory = Path(
        arguments.model_directory
    ).resolve()

    evaluation_directory = Path(
        arguments.evaluation_directory
    ).resolve()

    model_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    evaluation_directory.mkdir(
        parents=True,
        exist_ok=True,
    )

    dataframe, dataset_path = (
        load_dataset(
            arguments.dataset
        )
    )

    (
        train_data,
        validation_data,
        test_data,
    ) = chronological_transaction_split(
        dataframe
    )

    train_features = train_data[
        MODEL_FEATURES
    ]

    train_targets = train_data[
        TARGET_COLUMN
    ]

    candidate_models = (
        build_model_candidates()
    )

    fitted_models = {}
    validation_results = {}

    print(
        "Training candidate models..."
    )

    for model_name, pipeline in (
        candidate_models.items()
    ):
        print(f"  Training {model_name}...")

        pipeline.fit(
            train_features,
            train_targets,
        )

        (
            validation_metrics,
            _validation_probabilities,
            _validation_predictions,
        ) = evaluate_pipeline(
            pipeline=pipeline,
            dataframe=validation_data,
        )

        fitted_models[
            model_name
        ] = pipeline

        validation_results[
            model_name
        ] = validation_metrics

        print(
            f"    F1: "
            f"{validation_metrics['f1']:.4f}"
        )

        print(
            f"    Brier: "
            f"{validation_metrics['brier_score']:.4f}"
        )

    selected_model_name = (
        choose_best_model(
            validation_results
        )
    )

    selected_pipeline = (
        fitted_models[
            selected_model_name
        ]
    )

    print(
        "Selected model: "
        f"{selected_model_name}"
    )

    test_results = {}
    test_outputs = {}

    for model_name, pipeline in (
        fitted_models.items()
    ):
        (
            metrics,
            probabilities,
            predictions,
        ) = evaluate_pipeline(
            pipeline=pipeline,
            dataframe=test_data,
        )

        test_results[
            model_name
        ] = metrics

        test_outputs[
            model_name
        ] = {
            "probabilities": (
                probabilities
            ),
            "predictions": predictions,
        }

    (
        baseline_metrics,
        baseline_probabilities,
        baseline_predictions,
        baseline_test_data,
    ) = evaluate_baseline(test_data)

    if baseline_metrics is not None:
        test_results[
            "rule_based_baseline"
        ] = baseline_metrics

    model_path = (
        model_directory
        / "completion_pipeline.joblib"
    )

    joblib.dump(
        selected_pipeline,
        model_path,
    )

    selected_outputs = test_outputs[
        selected_model_name
    ]

    confusion_matrix_path = (
        evaluation_directory
        / "confusion_matrix.png"
    )

    save_confusion_matrix(
        targets=test_data[
            TARGET_COLUMN
        ].to_numpy(),
        predictions=(
            selected_outputs[
                "predictions"
            ]
        ),
        model_name=selected_model_name,
        output_path=confusion_matrix_path,
    )

    calibration_path = (
        evaluation_directory
        / "calibration_plot.png"
    )

    baseline_targets = None

    if baseline_test_data is not None:
        baseline_targets = (
            baseline_test_data[
                TARGET_COLUMN
            ].to_numpy()
        )

    save_calibration_plot(
        model_probabilities=(
            selected_outputs[
                "probabilities"
            ]
        ),
        baseline_probabilities=(
            baseline_probabilities
        ),
        targets=test_data[
            TARGET_COLUMN
        ].to_numpy(),
        baseline_targets=baseline_targets,
        model_name=selected_model_name,
        output_path=calibration_path,
    )

    predictions_path = (
        evaluation_directory
        / "test_predictions.csv"
    )

    save_test_predictions(
        test_data=test_data,
        selected_model_name=(
            selected_model_name
        ),
        model_probabilities=(
            selected_outputs[
                "probabilities"
            ]
        ),
        model_predictions=(
            selected_outputs[
                "predictions"
            ]
        ),
        baseline_probabilities=(
            baseline_probabilities
        ),
        output_path=predictions_path,
    )

    report = {
        "model_version": MODEL_VERSION,
        "generated_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "dataset_path": str(
            dataset_path
        ),
        "dataset_sources": sorted(
            dataframe[
                "dataset_source"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        ),
        "dataset_rows": int(
            len(dataframe)
        ),
        "split_strategy": (
            "Chronological 70/15/15 split grouped "
            "by donation_id"
        ),
        "dataset_splits": {
            "train": split_summary(
                train_data
            ),
            "validation": split_summary(
                validation_data
            ),
            "test": split_summary(
                test_data
            ),
        },
        "input_features": {
            "numeric": NUMERIC_FEATURES,
            "categorical": (
                CATEGORICAL_FEATURES
            ),
        },
        "excluded_leakage_columns": sorted(
            FORBIDDEN_MODEL_FEATURES
        ),
        "selection_rule": (
            "Lowest validation Brier score, "
            "then highest validation F1"
        ),
        "selected_model": (
            selected_model_name
        ),
        "validation_results": (
            validation_results
        ),
        "test_results": test_results,
        "baseline_threshold": (
            BASELINE_THRESHOLD
        ),
        "limitations": [
            (
                "The current dataset is synthetic."
            ),
            (
                "Metrics demonstrate technical "
                "feasibility, not real-world "
                "predictive validity."
            ),
            (
                "The model only scores receivers that "
                "already passed hard eligibility rules."
            ),
        ],
    }

    evaluation_json_path = (
        evaluation_directory
        / "evaluation_report.json"
    )

    write_json(
        evaluation_json_path,
        report,
    )

    evaluation_markdown_path = (
        evaluation_directory
        / "evaluation_report.md"
    )

    write_markdown_report(
        report=report,
        output_path=(
            evaluation_markdown_path
        ),
    )

    model_metadata = {
        "model_version": MODEL_VERSION,
        "model_name": selected_model_name,
        "trained_at": datetime.now(
            timezone.utc
        ).isoformat(),
        "artifact_path": str(
            model_path
        ),
        "artifact_sha256": (
            file_sha256(model_path)
        ),
        "dataset_path": str(
            dataset_path
        ),
        "dataset_source": sorted(
            dataframe[
                "dataset_source"
            ]
            .dropna()
            .astype(str)
            .unique()
            .tolist()
        ),
        "training_rows": int(
            len(train_data)
        ),
        "validation_rows": int(
            len(validation_data)
        ),
        "test_rows": int(
            len(test_data)
        ),
        "numeric_features": (
            NUMERIC_FEATURES
        ),
        "categorical_features": (
            CATEGORICAL_FEATURES
        ),
        "target": TARGET_COLUMN,
        "positive_class": (
            "confirmed completion"
        ),
        "prediction_threshold": 0.50,
        "python_version": (
            platform.python_version()
        ),
        "pandas_version": (
            pd.__version__
        ),
        "numpy_version": np.__version__,
        "scikit_learn_version": (
            sklearn.__version__
        ),
        "joblib_version": (
            joblib.__version__
        ),
        "synthetic_data_warning": (
            "This model was trained on synthetic data "
            "and is an experimental prototype."
        ),
    }

    model_metadata_path = (
        model_directory
        / "model_metadata.json"
    )

    write_json(
        model_metadata_path,
        model_metadata,
    )

    selected_metrics = (
        test_results[
            selected_model_name
        ]
    )

    print()
    print(
        "Training completed successfully."
    )

    print(
        f"Selected model: "
        f"{selected_model_name}"
    )

    print(
        f"Test precision: "
        f"{selected_metrics['precision']:.4f}"
    )

    print(
        f"Test recall: "
        f"{selected_metrics['recall']:.4f}"
    )

    print(
        f"Test F1: "
        f"{selected_metrics['f1']:.4f}"
    )

    print(
        f"Test ROC-AUC: "
        f"{selected_metrics['roc_auc']:.4f}"
    )

    print(
        f"Test Brier score: "
        f"{selected_metrics['brier_score']:.4f}"
    )

    print(
        f"Pipeline: {model_path}"
    )

    print(
        f"Metadata: {model_metadata_path}"
    )

    print(
        "Evaluation report: "
        f"{evaluation_json_path}"
    )

    print(
        "Confusion matrix: "
        f"{confusion_matrix_path}"
    )

    print(
        "Calibration plot: "
        f"{calibration_path}"
    )


if __name__ == "__main__":
    try:
        main()
    except Exception as error:
        print(
            f"Training failed: {error}",
            file=sys.stderr,
        )

        raise