"""Inspect task definition for the CTI-MCQ benchmark (https://arxiv.org/pdf/2406.07599)."""

from inspect_ai import Task, task
from inspect_ai.scorer import choice
from inspect_ai.solver import multiple_choice, system_message

from cti_mcq.dataset import load_dataset

SYSTEM_MESSAGE = "You are a security expert who answers questions."


@task
def cti_mcq() -> Task:
    """CTI-MCQ: Task to evaluate LLMs using Cyber Threat Intelligence Multiple Choice Questions."""
    return Task(
        dataset=load_dataset("cti_mcq"),
        solver=[system_message(SYSTEM_MESSAGE), multiple_choice()],
        scorer=choice(),
    )
