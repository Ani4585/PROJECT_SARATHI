import re

STOP_WORDS = {'what', 'does', 'is', 'a', 'an', 'the', 'in', 'of', 'to', 'for', 'with', 'on', 'at', 'and', 'or', 'it', 'this', 'that', 'how', 'why', 'who', 'where', 'can', 'you', 'based', 'from'}

class EvaluationEngine:
    @staticmethod
    def _extract_meaningful_words(text: str) -> set:
        if not text:
            return set()
        words = set(re.findall(r'\b\w+\b', text.lower()))
        return words - STOP_WORDS

    @staticmethod
    def calculate_context_relevance(query: str, context: str) -> float:
        q_words = EvaluationEngine._extract_meaningful_words(query)
        if not q_words:
            return 1.0
        c_words = EvaluationEngine._extract_meaningful_words(context)
        if not c_words:
            return 0.0

        matches = 0
        for qw in q_words:
            if any(qw in cw or cw in qw for cw in c_words):
                matches += 1
        return matches / len(q_words)

    @staticmethod
    def calculate_faithfulness(answer: str, context: str) -> float:
        a_words = EvaluationEngine._extract_meaningful_words(answer)
        if not a_words:
            return 1.0
        c_words = EvaluationEngine._extract_meaningful_words(context)
        if not c_words:
            return 0.0

        grounded = 0
        for aw in a_words:
            if any(aw in cw or cw in aw for cw in c_words):
                grounded += 1
        return grounded / len(a_words)

    @staticmethod
    def calculate_answer_relevance(query: str, answer: str) -> float:
        return EvaluationEngine.calculate_context_relevance(query, answer)
