"""Tests for the CTI-MCQ dataset adapter and evaluation pipeline."""

import csv
from pathlib import Path
from unittest.mock import Mock

import pytest
from inspect_ai import eval
from inspect_ai.model import ModelOutput, get_model

from cti_mcq.cti_mcq import SYSTEM_MESSAGE, cti_mcq
from cti_mcq.dataset import (
    DATASET_FILE,
    DATASET_SHA256,
    DATASET_URL,
    _ensure_dataset_file,
    load_dataset,
    record_to_sample_mcq,
)


@pytest.mark.parametrize("target", ["A", "B", "C", "D"])
def test_record_to_sample_mcq(target: str) -> None:
    record = {
        "Prompt": "Which protocol encrypts web traffic? A: HTTP B: HTTPS C: FTP D: DNS",
        "GT": target,
    }

    sample = record_to_sample_mcq(record)

    assert sample.input == record["Prompt"]
    assert sample.choices == ["A", "B", "C", "D"]
    assert sample.target == target


def test_record_to_sample_converts_prompt_to_string() -> None:
    sample = record_to_sample_mcq({"Prompt": 123, "GT": "A"})

    assert sample.input == "123"


def test_existing_dataset_does_not_download(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    csv_file = tmp_path / "cti-mcq.csv"
    csv_file.write_text("Prompt,GT\nQuestion,A\n", encoding="utf-8")
    download = Mock(side_effect=AssertionError("Unexpected dataset download"))
    monkeypatch.setattr("cti_mcq.dataset.download", download)

    assert _ensure_dataset_file(csv_file) == csv_file
    download.assert_not_called()


def test_load_local_dataset(monkeypatch: pytest.MonkeyPatch) -> None:
    assert DATASET_FILE.is_file()
    monkeypatch.setattr(
        "cti_mcq.dataset.download",
        Mock(side_effect=AssertionError("Unexpected dataset download")),
    )

    dataset = load_dataset("cti_mcq")

    assert len(dataset) > 0
    ids = [sample.id for sample in dataset]
    assert all(sample_id is not None for sample_id in ids)
    assert len(set(ids)) == len(ids)
    for sample in dataset:
        assert isinstance(sample.input, str)
        assert sample.input.strip()
        assert sample.choices == ["A", "B", "C", "D"]
        assert isinstance(sample.target, str)
        assert sample.target.upper() in ("A", "B", "C", "D")


def test_missing_dataset_downloads_and_converts(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    source = tmp_path / "source.tsv"
    source.write_text(
        "Prompt\tGT\n"
        "Question. Return your answer as a single uppercase letter: A, B, C, or D. "
        "**Important:** The last line of your answer should contain only "
        "the single letter corresponding to the best option, with no additional text.\tB\n",
        encoding="utf-8",
    )
    download = Mock(return_value=source)
    monkeypatch.setattr("cti_mcq.dataset.download", download)
    destination = tmp_path / "dataset" / "cti_mcq.csv"

    assert _ensure_dataset_file(destination) == destination

    download.assert_called_once()
    url, checksum, target = download.call_args.args
    assert url == DATASET_URL
    assert checksum == DATASET_SHA256
    assert target.name == "cti-mcq.tsv"
    with destination.open(encoding="utf-8", newline="") as file:
        [record] = list(csv.DictReader(file))
    assert record["GT"] == "B"
    assert "'ANSWER: <answer>'" in record["Prompt"]
    assert "Return your answer as a single uppercase letter" not in record["Prompt"]


@pytest.mark.parametrize("correct", [True, False], ids=["correct", "incorrect"])
def test_cti_mcq_scoring(correct: bool, tmp_path: Path) -> None:
    """Exercise the real solver and scorer without making model API calls."""
    task = cti_mcq()
    target = task.dataset[0].target
    answer = target if correct else next(c for c in "ABCD" if c != target)

    [log] = eval(
        tasks=task,
        model=get_model(
            "mockllm/model",
            custom_outputs=[
                ModelOutput.from_content("mockllm/model", f"ANSWER: {answer}")
            ],
        ),
        limit=1,
        epochs=1,
        log_dir=str(tmp_path),
    )

    assert log.status == "success", log.error
    assert log.results is not None
    assert log.results.scores[0].metrics["accuracy"].value == float(correct)
    assert log.samples is not None
    assert len(log.samples) == 1
    assert any(
        message.role == "system" and message.content == SYSTEM_MESSAGE
        for message in log.samples[0].messages
    )
