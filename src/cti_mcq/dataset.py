"""Dataset loading and sample adapters for the CTI-MCQ benchmark."""

import csv
from pathlib import Path
from tempfile import TemporaryDirectory
from typing import Any

from inspect_ai.dataset import Dataset, Sample, csv_dataset
from inspect_ai.util import download

DATASET_FILE = Path(__file__).parent / "dataset" / "cti_mcq.csv"
DATASET_REVISION = "4543e5b6560d3204e1205ced4fa286adc7452d07"
DATASET_URL = (
    "https://raw.githubusercontent.com/maveryn/cti-bench/"
    f"{DATASET_REVISION}/data/cti-mcq.tsv"
)
DATASET_SHA256 = "11e0af8db2dae9706c6e79901d2390bcdf9746e8feccbd9ba10682df649bcc6a"


def _ensure_dataset_file(csv_file: Path = DATASET_FILE) -> Path:
    """Download and convert the upstream TSV when the local CSV is absent."""
    if csv_file.is_file():
        return csv_file

    with TemporaryDirectory() as temp_dir:
        downloaded_file = download(
            DATASET_URL,
            DATASET_SHA256,
            Path(temp_dir) / "cti-mcq.tsv",
        )
        with downloaded_file.open(encoding="utf-8", newline="") as source:
            reader = csv.DictReader(source, delimiter="\t")
            fieldnames = reader.fieldnames
            rows = list(reader)

    for row in rows:
        row["Prompt"] = (
            row["Prompt"]
            .replace(
                "Return your answer as a single uppercase letter: A, B, C, or D. ",
                "",
            )
            .replace(
                "**Important:** The last line of your answer should contain only "
                "the single letter corresponding to the best option, with no additional text.",
                "**Important:** The last line of your answer should contain only "
                "'ANSWER: <answer>' where <answer> is a single uppercase letter "
                "corresponding to the best option, with no additional text.",
            )
        )

    csv_file.parent.mkdir(parents=True, exist_ok=True)
    with csv_file.open("w", encoding="utf-8", newline="") as destination:
        writer = csv.DictWriter(destination, fieldnames=fieldnames or [])
        writer.writeheader()
        writer.writerows(rows)
    return csv_file


def load_dataset(task_name: str) -> Dataset:
    """Load the CTI-MCQ dataset using the corresponding adapter."""
    if task_name == "cti_mcq":
        dataset = csv_dataset(
            csv_file=str(_ensure_dataset_file()),
            sample_fields=record_to_sample_mcq,
            auto_id=True,
        )

    return dataset


def record_to_sample_mcq(record: dict[str, Any]) -> Sample:
    """Convert a CTI-MCQ record (URL,Question,Option A,Option B,Option C,Option D,Prompt,GT) into an Inspect sample."""
    return Sample(
        input=str(record["Prompt"]),
        choices=["A", "B", "C", "D"],
        target=record["GT"],
    )
