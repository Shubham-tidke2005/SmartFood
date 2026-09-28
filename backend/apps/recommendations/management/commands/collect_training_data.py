import json

from pathlib import Path

from django.conf import settings
from django.core.management.base import (
    BaseCommand,
    CommandError,
)

from apps.recommendations.models import (
    MatchTrainingRecord,
)
from apps.recommendations.training_data import (
    collect_training_records,
    export_training_dataset,
)


class Command(BaseCommand):
    help = (
        "Collect resolved approved match outcomes and "
        "export the SmartFood ML training dataset."
    )

    def add_arguments(self, parser):
        parser.add_argument(
            "--source",
            required=True,
            choices=[
                choice
                for choice, _label
                in MatchTrainingRecord
                .DatasetSource.choices
            ],
            help=(
                "Source of the selected transaction data. "
                "REAL, SYNTHETIC or PILOT."
            ),
        )

        parser.add_argument(
            "--output-directory",
            default=None,
            help=(
                "Optional dataset output directory. "
                "Defaults to ml/data/processed."
            ),
        )

        parser.add_argument(
            "--collect-only",
            action="store_true",
            help=(
                "Collect database records without "
                "exporting CSV and metadata."
            ),
        )

    def handle(self, *args, **options):
        source = options["source"]

        statistics = collect_training_records(
            dataset_source=source,
        )

        self.stdout.write(
            self.style.SUCCESS(
                "Training records collected."
            )
        )

        self.stdout.write(
            json.dumps(
                statistics,
                indent=2,
            )
        )

        if statistics["source_conflict"] > 0:
            self.stdout.write(
                self.style.WARNING(
                    "Some records already exist with a "
                    "different dataset source. They were "
                    "not changed."
                )
            )

        if options["collect_only"]:
            return

        output_directory = (
            options["output_directory"]
        )

        if output_directory:
            output_path = Path(
                output_directory
            )
        else:
            output_path = (
                settings.BASE_DIR.parent
                / "ml"
                / "data"
                / "processed"
            )

        try:
            result = export_training_dataset(
                csv_path=(
                    output_path
                    / "smartfood_training_data.csv"
                ),
                metadata_path=(
                    output_path
                    / "smartfood_training_metadata.json"
                ),
            )
        except OSError as error:
            raise CommandError(
                f"Could not export dataset: {error}"
            ) from error

        self.stdout.write(
            self.style.SUCCESS(
                f"Exported {result['row_count']} rows."
            )
        )

        self.stdout.write(
            f"CSV: {result['csv_path']}"
        )

        self.stdout.write(
            "Metadata: "
            f"{result['metadata_path']}"
        )