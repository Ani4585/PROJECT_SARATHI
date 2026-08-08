"""
Unit and Integration Tests for Milestone 60: Autonomous AI Agent Continuous Evaluation & Hallucination Guardrails.
Tag: v2.4.0-eval-guardrails-engine
"""
import pytest
from sarathi.eval import EvaluationEngine, HallucinationGuardrail, HallucinationDetectedError, EvalManager

def test_evaluation_engine_metrics():
    query = "What is Project Sarathi?"
    context = "Project Sarathi is an enterprise asynchronous platform framework."
    answer = "Sarathi is an enterprise asynchronous platform."

    c_rel = EvaluationEngine.calculate_context_relevance(query, context)
    assert c_rel > 0.5

    faith = EvaluationEngine.calculate_faithfulness(answer, context)
    assert faith >= 0.8

def test_hallucination_guardrails_pass_and_reject():
    guardrail = HallucinationGuardrail(min_faithfulness_threshold=0.60)
    context = "Project Sarathi features vector search and task DAG workflows."

    valid_answer = "Sarathi supports vector search and task DAG workflows."
    is_valid, score = guardrail.validate_and_guard(valid_answer, context)
    assert is_valid
    assert score >= 0.60

    hallucinated_answer = "Sarathi contains quantum cryptography rocket engines for Mars space probes."
    try:
        guardrail.validate_and_guard(hallucinated_answer, context)
        assert False, "Should raise HallucinationDetectedError"
    except HallucinationDetectedError:
        assert True

def test_eval_manager_composite_report():
    mgr = EvalManager(min_faithfulness=0.60)
    report = mgr.evaluate_response(
        query="What features does Sarathi provide?",
        answer="Sarathi provides vector search and task workflows.",
        context="Sarathi provides vector search, task workflows, and multi-tenant security."
    )

    assert report["is_safe"]
    assert report["context_relevance"] > 0.5
    assert report["faithfulness"] > 0.70
    assert report["composite_score"] > 0.50
