"""Phase B: local-v2-eval judge — parse, refuse, explicit-only scoring."""

from __future__ import annotations

import json

import pytest

from time_machine.domain import JudgeScore, UserAnnotations
from time_machine.errors import RegistryError
from time_machine.evaluation_judge import BANNER, EVAL_PROTOCOL, JudgeEvaluator, JudgeService
from time_machine.judge_prompts import (
    hash_judge_input,
    load_judge_config,
    load_rubric,
    parse_judge_reply,
    render_judge_input,
)
from time_machine.runners.fake import FakeRunner
from time_machine.trip_controller import TripController
from tests.conftest import REPO_ROOT, make_cohort, make_model


def test_parse_score_and_unscored():
    assert parse_judge_reply("SCORE: 8") == ("scored", 8, "")
    assert parse_judge_reply("SCORE: 10\n") == ("scored", 10, "")
    assert parse_judge_reply("UNSCORED: private unpublished fact")[0] == "unscored"
    assert parse_judge_reply("UNSCORED")[0] == "unscored"
    assert parse_judge_reply("unscored")[0] == "unscored"
    assert parse_judge_reply("hello")[0] == "unscored"
    assert parse_judge_reply("SCORE: 99")[0] == "unscored"
    assert parse_judge_reply("")[0] == "unscored"
    status, score, reason = parse_judge_reply("UNSCORED")
    assert status == "unscored" and score is None and reason


def test_rubric_and_judge_config_load():
    rubric = load_rubric(REPO_ROOT / "registry" / "judges" / "rubric-v1.yaml")
    assert rubric["id"] == "judge-rubric-v1"
    assert "output_contract" in rubric
    cfg = load_judge_config(REPO_ROOT / "registry" / "judges" / "judge-v1.yaml")
    assert cfg["judge_model_id"]
    assert cfg["rubric_id"] == "judge-rubric-v1"
    assert cfg["judge_model_id"] != "qwen25-7b-instruct-2024"  # not status-quo slot


def test_judge_input_is_visible_and_hashed():
    rubric = load_rubric(REPO_ROOT / "registry" / "judges" / "rubric-v1.yaml")
    text = render_judge_input(
        rubric,
        raw_prompt="SECRET_PROMPT",
        success_criterion="be right",
        model_id="gpt2-2019",
        display_year=2019,
        output_text="OUT_TEXT",
    )
    assert "SECRET_PROMPT" in text
    assert "OUT_TEXT" in text
    assert "judge-rubric-v1" in text
    assert "SCORE:" in text or "SCORE" in text
    assert hash_judge_input(text) == hash_judge_input(text)
    assert len(hash_judge_input(text)) == 64


def test_judge_score_validation():
    JudgeScore(
        model_id="a",
        trip_id="t",
        status="scored",
        score_1_10=7,
        rubric_id="judge-rubric-v1",
        judge_model_id="flan-t5-large-2022",
    )
    with pytest.raises(Exception):
        JudgeScore(
            model_id="a",
            trip_id="t",
            status="scored",
            score_1_10=11,
            rubric_id="r",
            judge_model_id="j",
        )


def test_evaluator_does_not_autoscore():
    from time_machine.domain import TripManifest

    svc = JudgeService(paths=None) if False else None
    ev = JudgeEvaluator(service=object())  # type: ignore
    assert ev.evaluate_run(None, "x") == {}
    m = TripManifest(protocol_version="local-v1", cohort_id="c", app_version="1", raw_prompt_sha256="0" * 64)
    result = ev.evaluate_trip(m)
    assert result["judge"] == "not_run"
    assert "EXPERIMENTAL" in result.get("banner", BANNER)
    assert "EXPERIMENTAL" in BANNER


def test_score_trip_with_scripted_judge(store, paths, monkeypatch):
    cohort = make_cohort(
        [
            make_model("a", 2019, "A", "base_continuation", "identity-v1"),
            make_model("b", 2024, "B", "chat", "fake-chat-v1"),
        ]
    )

    class F:
        def create(self, kind="composite"):
            return FakeRunner()

        def create_for_spec(self, spec):
            return FakeRunner()

        def verify_artifact(self, spec):
            from time_machine.domain import RunnerAvailability

            return RunnerAvailability(available=True, reason="ok")

        def preflight(self, spec):
            from time_machine.domain import RunnerAvailability

            return RunnerAvailability(available=True, reason="ok")

    controller = TripController(
        cohort=cohort, store=store, factory=F(), paths=paths, runner_kind="fake"
    )
    manifest = controller.run_trip("judge me", block_network_during_trip=False)
    assert manifest.complete

    judge = JudgeService(paths=paths, factory=F())
    # script judge generation without real weights
    replies = {"a": "SCORE: 3", "b": "UNSCORED: private unpublished fact"}

    def fake_generate(prepared_text: str) -> str:
        # crude: pick by which model id appears in judge input
        if "historical model a" in prepared_text or "model a," in prepared_text or "(historical model a" in prepared_text:
            return replies["a"]
        # score_run embeds model_id in header
        if "a," in prepared_text.split("Candidate output")[0] or "model a" in prepared_text.lower():
            # fallback order
            pass
        if "historical model b" in prepared_text or "model b," in prepared_text:
            return replies["b"]
        # default: first unseen
        return "SCORE: 5"

    monkeypatch.setattr(judge, "_generate", fake_generate)
    # ensure cache dir exists so we don't hit LoadError path if _generate bypassed
    scores = []
    for run in manifest.runs:
        out = store.read_output(manifest.trip_id, run.model_id)
        # force reliable mapping via dedicated generate stub keyed by run
        monkeypatch.setattr(
            judge,
            "_generate",
            lambda prepared_text, _m=run.model_id: (
                "SCORE: 3" if _m == "a" else "UNSCORED: private unpublished fact"
            ),
        )
        scores.append(
            judge.score_run(
                trip_id=manifest.trip_id,
                run=run,
                raw_prompt="judge me",
                success_criterion="",
                output_text=out,
            )
        )

    assert scores[0].status == "scored" and scores[0].score_1_10 == 3
    assert scores[1].status == "unscored"
    assert "private" in scores[1].unscored_reason
    assert scores[0].protocol == EVAL_PROTOCOL
    assert scores[0].rubric_id == "judge-rubric-v1"

    # artifacts on disk
    sdir = judge.score_dir(manifest.trip_id, "a")
    assert (sdir / "judge-input.txt").is_file()
    assert (sdir / "judge-output.txt").is_file()
    assert (sdir / "score.json").is_file()
    data = json.loads((sdir / "score.json").read_text(encoding="utf-8"))
    assert data["score_1_10"] == 3
    assert data["judge_model_id"]

    loaded = judge.read_scores(manifest.trip_id)
    assert len(loaded) == 2


def test_trip_run_does_not_create_judge_artifacts(store, paths):
    """local-v1 trip path must stay judge-free until explicit score."""
    cohort = make_cohort([make_model("a", 2019, "A", "base_continuation", "identity-v1")])

    class F:
        def create(self, kind="composite"):
            return FakeRunner()

        def create_for_spec(self, spec):
            return FakeRunner()

        def verify_artifact(self, spec):
            from time_machine.domain import RunnerAvailability

            return RunnerAvailability(available=True, reason="ok")

        def preflight(self, spec):
            from time_machine.domain import RunnerAvailability

            return RunnerAvailability(available=True, reason="ok")

    controller = TripController(
        cohort=cohort, store=store, factory=F(), paths=paths, runner_kind="fake"
    )
    manifest = controller.run_trip("no silent judge", block_network_during_trip=False)
    assert not (paths.judge_dir / manifest.trip_id).exists()


def test_missing_rubric_raises(tmp_path):
    with pytest.raises(RegistryError):
        load_rubric(tmp_path / "nope.yaml")
    with pytest.raises(RegistryError):
        load_judge_config(tmp_path / "nope.yaml")
