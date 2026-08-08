"""
Master Evaluation & Guardrails Manager.
"""
from typing import Dict, Any
from sarathi.eval.evaluator import EvaluationEngine
from sarathi.eval.guardrails import HallucinationGuardrail, HallucinationDetectedError

class EvalManager:
    def __init__(self, min_faithfulness: float = 0.60):
        self.evaluator = EvaluationEngine()
        self.guardrail = HallucinationGuardrail(min_faithfulness_threshold=min_faithfulness)

    def evaluate_response(self, query: str, answer: str, context: str) -> Dict[str, Any]:
        c_rel = self.evaluator.calculate_context_relevance(query, context)
        faith = self.evaluator.calculate_faithfulness(answer, context)
        a_rel = self.evaluator.calculate_answer_relevance(query, answer)

        is_safe = faith >= self.guardrail.min_faithfulness_threshold

        return {
            "is_safe": is_safe,
            "context_relevance": c_rel,
            "faithfulness": faith,
            "answer_relevance": a_rel,
            "composite_score": (c_rel + faith + a_rel) / 3.0
        }
