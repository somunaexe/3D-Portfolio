"""The golden question set must keep passing: this is the regression net for retrieval changes."""
import sys
from pathlib import Path

import pytest

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
import evaluate  # noqa: E402
import indexing  # noqa: E402
import query  # noqa: E402
from fakes import FakeLLM  # noqa: E402


@pytest.fixture(scope="module")
def db_dir(tmp_path_factory):
    path = tmp_path_factory.mktemp("chroma")
    indexing.index_chunks(indexing.build_chunks(), db_dir=path)
    return path


def test_every_golden_case_is_well_formed():
    for case in evaluate.load_cases():
        assert case["question"].strip() and len(case["question"]) <= 200
        assert set(case) <= {"question", "retrieved", "retrieved_any", "mention", "not_mention", "unsupported", "note"}


def test_retrieval_passes_every_golden_case(db_dir):
    failures = [(case["question"], problems) for case, problems in evaluate.run(evaluate.load_cases(), db_dir=db_dir) if problems]
    assert failures == []


def test_a_retrieval_miss_is_reported():
    case = {"question": "What is Somuna's favourite food?", "retrieved": ["Full Stack Developer at Bulfighter"]}
    assert evaluate.check_retrieval(case) == ["retrieval missed 'Full Stack Developer at Bulfighter'"]


def answer_with(text, sources=()):
    return query.Answer(answer=text, sources=list(sources), retrieved=[])


def test_answer_checks_catch_missing_forbidden_and_unsupported_wording():
    case = {"question": "q", "mention": ["React"], "not_mention": ["PhD"], "unsupported": True}
    problems = evaluate.check_answer(case, answer_with("They have a PhD [1].", sources=[{"id": "x"}]))
    assert len(problems) == 3
    assert evaluate.check_answer(case, answer_with("React is used. I don't have more.")) == []


def test_running_with_answers_calls_the_model_and_checks_it(db_dir):
    cases = [{"question": "What did Somuna do at Bulfighter?", "mention": ["React"]}]
    good = evaluate.run(cases, answers=True, llm=FakeLLM(answer="They used React [1].").runnable, db_dir=db_dir)
    bad = evaluate.run(cases, answers=True, llm=FakeLLM(answer="I don't know.").runnable, db_dir=db_dir)
    assert good[0][1] == [] and bad[0][1] == ["answer does not mention 'React'"]
