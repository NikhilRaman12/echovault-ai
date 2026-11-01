"""Automated test runner executing declarative YAML test specifications for EchoVault AI."""

import json
from pathlib import Path
import pytest
import yaml

from echovault.agents.intake_agent import intake_agent, IntakeValidationError
from echovault.database import db
from echovault.orchestrator import orchestrator
from echovault.services.export_service import export_service
from echovault.services.storage_service import storage_service

YAML_PATH = Path(__file__).parent / "test_cases.yaml"


@pytest.fixture(scope="module")
def yaml_specs():
    """Load declarative test suite specifications from YAML."""
    with open(YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def test_yaml_intake_validation(yaml_specs):
    """Execute all intake validation test cases defined in YAML."""
    intake_category = next(c for c in yaml_specs["test_categories"] if c["category"] == "intake_validation")
    for case in intake_category["cases"]:
        case_id = case["id"]
        inp = case["input"]
        exp = case["expected"]

        if exp.get("raises_error"):
            with pytest.raises(IntakeValidationError):
                if "filename" in inp:
                    intake_agent.process_audio_input(
                        file_bytes=b"dummy bytes",
                        original_filename=inp["filename"],
                    )
                else:
                    intake_agent.process_text_input(
                        content=inp["content"],
                        narrator=inp.get("narrator"),
                    )
        else:
            state = intake_agent.process_text_input(
                content=inp["content"],
                narrator=inp.get("narrator"),
            )
            assert state.memory_id is not None
            assert state.processing_status.value == exp["status"]


def test_yaml_deduplication(yaml_specs):
    """Execute deduplication test cases from YAML."""
    dedup_category = next(c for c in yaml_specs["test_categories"] if c["category"] == "deduplication")
    for case in dedup_category["cases"]:
        content = case["input"]["content"]
        content_hash = storage_service.compute_sha256(content)
        existing = db.find_duplicate_by_hash(content_hash)
        expected_dup = case["expected"]["duplicate_found"]
        
        if expected_dup:
            assert existing is not None, f"Expected duplicate for {case['id']}"
        else:
            assert existing is None, f"Expected no duplicate for {case['id']}"


def test_yaml_fts5_retrieval(yaml_specs):
    """Execute FTS5 search retrieval test cases from YAML."""
    search_category = next(c for c in yaml_specs["test_categories"] if c["category"] == "fts5_retrieval")
    for case in search_category["cases"]:
        query = case["query"]
        exp = case["expected"]
        results = db.search_memories(query, limit=5)

        if "min_results" in exp:
            assert len(results) >= exp["min_results"], f"{case['id']} expected at least {exp['min_results']} results"
        if "max_results" in exp:
            assert len(results) <= exp["max_results"], f"{case['id']} expected at most {exp['max_results']} results"
        if "expected_title_contains" in exp:
            assert any(exp["expected_title_contains"].lower() in r.title.lower() for r in results), (
                f"{case['id']} expected title to contain '{exp['expected_title_contains']}'"
            )


def test_yaml_grounded_qa(yaml_specs):
    """Execute grounded question answering and abstention test cases from YAML."""
    qa_category = next(c for c in yaml_specs["test_categories"] if c["category"] == "grounded_qa")
    for case in qa_category["cases"]:
        question = case["question"]
        exp = case["expected"]
        
        answer, traces = orchestrator.answer_question(question)

        if exp["is_abstention"]:
            assert answer.is_abstention is True, f"{case['id']} expected abstention for: {question}"
            assert answer.answer == exp["exact_abstention_text"], (
                f"{case['id']} expected exact abstention text: '{exp['exact_abstention_text']}' but got '{answer.answer}'"
            )
        else:
            assert answer.is_abstention is False, f"{case['id']} should have answered: {question}"
            assert len(answer.citations) > 0, f"{case['id']} should have provided citations"
            combined_text = (answer.answer + " " + " ".join(c.passage for c in answer.citations)).lower()
            must_contain_any = exp.get("must_contain_any", [])
            assert any(term.lower() in combined_text for term in must_contain_any), (
                f"{case['id']} expected to contain one of {must_contain_any}"
            )


def test_yaml_export_portability(yaml_specs):
    """Execute export and portability test cases from YAML."""
    exp_category = next(c for c in yaml_specs["test_categories"] if c["category"] == "export_portability")
    for case in exp_category["cases"]:
        exp = case["expected"]
        if "required_keys" in exp:
            export_dict = export_service.export_archive_to_dict()
            for key in exp["required_keys"]:
                assert key in export_dict, f"Missing key '{key}' in JSON export payload"
            assert export_dict["total_memories"] >= 6
        if "must_contain_heading" in exp:
            md_text = export_service.export_archive_to_markdown()
            assert exp["must_contain_heading"] in md_text
