"""
Attribute-Based Access Control (ABAC) & Policy Enforcement Engine.
"""
from enum import Enum
from typing import Dict, Any, List, Optional

class PolicyEffect(str, Enum):
    ALLOW = "ALLOW"
    DENY = "DENY"

class PolicyRule:
    def __init__(
        self,
        rule_id: str,
        subject_role: Optional[str] = None,
        action: Optional[str] = None,
        resource_type: Optional[str] = None,
        effect: PolicyEffect = PolicyEffect.ALLOW,
        conditions: Optional[Dict[str, Any]] = None
    ):
        self.rule_id = rule_id
        self.subject_role = subject_role
        self.action = action
        self.resource_type = resource_type
        self.effect = effect
        self.conditions = conditions or {}

class PolicyEngine:
    def __init__(self, default_effect: PolicyEffect = PolicyEffect.DENY):
        self.default_effect = default_effect
        self.rules: List[PolicyRule] = []

    def add_rule(self, rule: PolicyRule):
        self.rules.append(rule)

    def evaluate(self, subject: Dict[str, Any], action: str, resource: Dict[str, Any]) -> PolicyEffect:
        for rule in self.rules:
            if rule.subject_role and subject.get("role") != rule.subject_role:
                continue
            if rule.action and rule.action != action:
                continue
            if rule.resource_type and resource.get("type") != rule.resource_type:
                continue

            # Check attribute conditions
            match = True
            for ck, cv in rule.conditions.items():
                if resource.get(ck) != cv and subject.get(ck) != cv:
                    match = False
                    break

            if match:
                return rule.effect

        return self.default_effect
