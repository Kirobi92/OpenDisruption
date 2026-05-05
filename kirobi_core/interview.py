"""Guided onboarding interview.

The interview asks a fixed set of questions and stores the answers in
a :class:`~kirobi_core.config.Profile`. Sensitive questions (family,
finances, health) are written to a separate file under
``extracts/family-private/profiles/`` so the main profile remains
shareable.

The interview is fully scriptable: tests pass an iterator of canned
answers via the ``input_fn`` argument. A real CLI run uses
``input()``.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Callable, Iterable, Iterator

from .config import ConfigStore, Profile
from .zones import Zone


@dataclass(frozen=True)
class Question:
    """One interview question."""

    key: str
    prompt: str
    sensitive: bool = False
    default: str | None = None
    choices: tuple[str, ...] = ()


# A small, opinionated default question set covering hardware, goals,
# family, business, creativity and privacy preferences. Real
# deployments can extend this list.
DEFAULT_QUESTIONS: tuple[Question, ...] = (
    Question("display_name", "Wie sollen wir dich nennen?"),
    Question(
        "primary_goal",
        "Was ist dein wichtigstes Ziel mit Kirobi (Familie / Business / Kreativität / Lernen)?",
        choices=("familie", "business", "kreativität", "lernen", "anderes"),
        default="familie",
    ),
    Question(
        "hardware_profile",
        "Welche Hardware nutzt du? (z.B. 'Pop!_OS, RTX 4090, 64GB RAM')",
        default="linux-gpu",
    ),
    Question(
        "preferred_models",
        "Bevorzugte Modellgrößen lokal? (small / medium / large)",
        choices=("small", "medium", "large"),
        default="medium",
    ),
    Question(
        "quiet_hours",
        "Quiet Hours (Zeitraum ohne autonome Aktionen, z.B. '22:00-07:00'). Leer lassen für keine.",
        default="22:00-07:00",
    ),
    Question(
        "autonomy_level",
        "Wie autonom darf Kirobi handeln? (dry-run / propose / execute-with-approval)",
        choices=("dry-run", "propose", "execute-with-approval"),
        default="dry-run",
    ),
    Question(
        "share_with_cloud",
        "Dürfen WORKSPACE-Inhalte mit Cloud-LLMs (OpenAI/Anthropic) geteilt werden? (ja/nein)",
        choices=("ja", "nein"),
        default="nein",
    ),
    Question(
        "family_members",
        "Familienmitglieder, die Kirobi mit-bedienen (kommagetrennte Vornamen).",
        sensitive=True,
        default="",
    ),
    Question(
        "private_notes",
        "Sensible Notizen oder Wünsche, die nur lokal bleiben sollen (Enter = überspringen).",
        sensitive=True,
        default="",
    ),
)


def _default_input(prompt: str) -> str:
    return input(prompt)


def _default_print(line: str) -> None:
    print(line)


def _normalize_answer(question: Question, raw: str) -> str:
    answer = raw.strip()
    if not answer and question.default is not None:
        return question.default
    if question.choices and answer.lower() not in {c.lower() for c in question.choices}:
        # Accept anyway but record verbatim — the backlog generator can
        # surface mismatches later.
        return answer
    return answer


def run_interview(
    questions: Iterable[Question] = DEFAULT_QUESTIONS,
    *,
    input_fn: Callable[[str], str] = _default_input,
    output_fn: Callable[[str], None] = _default_print,
) -> tuple[dict[str, str], dict[str, str]]:
    """Run the interview and return ``(public_answers, sensitive_answers)``."""
    public: dict[str, str] = {}
    sensitive: dict[str, str] = {}
    for q in questions:
        choices_hint = f" [{'/'.join(q.choices)}]" if q.choices else ""
        default_hint = f" (Default: {q.default})" if q.default else ""
        sensitive_hint = " [SENSITIV — bleibt lokal]" if q.sensitive else ""
        prompt = f"{q.prompt}{choices_hint}{default_hint}{sensitive_hint}\n> "
        try:
            raw = input_fn(prompt)
        except EOFError:
            raw = ""
        answer = _normalize_answer(q, raw)
        if q.sensitive:
            sensitive[q.key] = answer
        else:
            public[q.key] = answer
    output_fn("Interview abgeschlossen.")
    return public, sensitive


def derive_config(public_answers: dict[str, str]) -> dict[str, object]:
    """Derive an agent / autonomy configuration from interview answers."""
    autonomy = public_answers.get("autonomy_level", "dry-run").strip().lower()
    cloud = public_answers.get("share_with_cloud", "nein").strip().lower() == "ja"
    quiet = public_answers.get("quiet_hours", "").strip()
    primary = public_answers.get("primary_goal", "familie").strip().lower()
    model_size = public_answers.get("preferred_models", "medium").strip().lower()

    priority_agents = {
        "familie": ["kirobi-core", "samira-heart", "sineo-creator"],
        "business": ["kirobi-core", "enterprise-agent", "research-crew"],
        "kreativität": ["kirobi-core", "creative-agent", "sineo-creator"],
        "lernen": ["kirobi-core", "research-crew", "kirobi-architect"],
    }.get(primary, ["kirobi-core", "kirobi-architect", "kirobi-coder"])

    return {
        "autonomy_level": autonomy,
        "allow_cloud_for_workspace": cloud,
        "quiet_hours": quiet,
        "preferred_model_size": model_size,
        "primary_goal": primary,
        "priority_agents": priority_agents,
        "default_dry_run": autonomy != "execute-with-approval",
    }


def run_and_save(
    store: ConfigStore,
    *,
    profile_name: str = "default",
    questions: Iterable[Question] = DEFAULT_QUESTIONS,
    input_fn: Callable[[str], str] = _default_input,
    output_fn: Callable[[str], None] = _default_print,
    sensitive_zone: Zone = Zone.FAMILY_PRIVATE,
) -> Path:
    """Run the interview and persist results, returning the profile path."""
    profile = store.load(profile_name)
    public, sensitive = run_interview(
        questions, input_fn=input_fn, output_fn=output_fn
    )
    profile.merge_answers(public)
    profile.derived.update(derive_config(public))
    if any(v for v in sensitive.values()):
        store.write_sensitive(profile, sensitive, zone=sensitive_zone)
    path = store.save(profile)
    output_fn(f"Profil gespeichert: {path}")
    if profile.sensitive_ref:
        output_fn(f"Sensible Antworten gespeichert in: {profile.sensitive_ref}")
    return path


# Convenience for tests: turn an iterable of strings into an input_fn.
def scripted_input(answers: Iterable[str]) -> Callable[[str], str]:
    """Return an ``input_fn`` that pops answers from *answers* in order."""
    it: Iterator[str] = iter(answers)

    def _fn(_prompt: str) -> str:
        try:
            return next(it)
        except StopIteration:
            return ""

    return _fn
