# CTI-MCQ Benchmark

An [Inspect AI](https://inspect.aisi.org.uk/) implementation of CTI-MCQ, the
multiple-choice knowledge task from
[CTIBench](https://arxiv.org/abs/2406.07599), a benchmark for evaluating language
models in Cyber Threat Intelligence (CTI).

The evaluation uses 2,500 questions with four answer options each. The model
selects an answer from A, B, C, or D, and Inspect reports accuracy using its
`choice()` scorer. Responses should have the format `ANSWER: <letter>`.

The dataset is bundled in `src/cti_mcq/dataset/cti_mcq.csv`. If it is missing,
the loader downloads a pinned upstream TSV, verifies its SHA-256 checksum,
and converts it to CSV with answer-format instructions adapted for Inspect.

## Installation

Python 3.11 or newer is required. Clone the repository and install the project
with [uv](https://docs.astral.sh/uv/):

```bash
git clone https://github.com/AI-Sec-dev/inspect-eval-cti_mcq.git
cd inspect-eval-cti_mcq
uv sync
```

## Usage

Set the credentials required by your model provider, then run:

```bash
uv run inspect eval cti_mcq/cti_mcq --model <provider/model>

# Limit the evaluation to ten samples
uv run inspect eval cti_mcq/cti_mcq --model <provider/model> --limit 10

# Evaluate a specific sample
uv run inspect eval cti_mcq/cti_mcq --model <provider/model> --sample-id 1
```

For example, run a smoke test with a mock model without model API credentials:

```bash
uv run inspect eval cti_mcq/cti_mcq --model mockllm/model --limit 10
```

Mock-model results check execution only; they do not measure model capability.
Inspect saves evaluation logs under `logs/` by default. View them with:

```bash
uv run inspect view
```

## Development

```bash
uv sync
uv run pytest tests/test_cti_mcq.py
uv run ruff check
uv run ruff format --check
```

The tests cover sample conversion, local dataset loading, reuse of an existing
dataset without downloading, and correct and incorrect answers through the
real solver and scorer with a mock model.

## Citation

If you use this evaluation, cite the original
[CTIBench paper](https://arxiv.org/abs/2406.07599):

```bibtex
@article{alam2024ctibench,
  title = {{CTIBench}: A Benchmark for Evaluating {LLMs} in Cyber Threat Intelligence},
  author = {Alam, Md Tanvirul and Bhusal, Dipkamal and Nguyen, Le and Rastogi, Nidhi},
  year = {2024},
  eprint = {2406.07599},
  archiveprefix = {arXiv},
  primaryclass = {cs.CR}
}
```

## License

This implementation is licensed under the [MIT License](LICENSE). The bundled
CTI-MCQ dataset may be subject to separate
[upstream terms](https://github.com/maveryn/cti-bench).
