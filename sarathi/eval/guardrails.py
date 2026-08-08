"""
Hallucination Guardrails Interceptor.
"""
from typing import Dict, Any, Tuple
from sarathi.eval.evaluator import EvaluationEngine

class HallucinationDetectedError(Exception):
    """Raised when an answer fails the faithfulness/groundedness threshold."""
    pass

class HallucinationGuardrail:
    def __init__(self, min_faithfulness_threshold: float = 0.60):
        self.min_faithfulness_threshold = min_faithfulness_threshold

    def validate_and_guard(self, answer: str, context: str) -> Tuple[bool, float]:
        score = EvaluationEngine.calculate_faithfulness(answer=answer, context=context)
        if score < self.min_faithfulness_threshold:
            raise HallucinationDetectedError(
                f"Hallucination detected: Faithfulness score {score:.2f} below threshold {self.min_faithfulness_threshold:.2f}."
            )
        return True, score
