"""
Master Governance & Compliance Manager.
"""
from typing import Dict, Any, Optional
from sarathi.governance.policy import PolicyEngine, PolicyRule, PolicyEffect
from sarathi.governance.audit import AuditLogger
from sarathi.governance.pii import PIIRedactor

class GovernanceManager:
    def __init__(self, default_policy_effect: PolicyEffect = PolicyEffect.DENY):
        self.policy_engine = PolicyEngine(default_effect=default_policy_effect)
        self.audit_logger = AuditLogger()
        self.pii_redactor = PIIRedactor()

    def authorize_and_log(
        self,
        subject: Dict[str, Any],
        action: str,
        resource: Dict[str, Any],
        entry_id: str
    ) -> PolicyEffect:
        effect = self.policy_engine.evaluate(subject, action, resource)
        self.audit_logger.log(
            entry_id=entry_id,
            actor=subject.get("id", "anonymous"),
            action=action,
            resource_id=resource.get("id", "unknown"),
            metadata={"effect": effect.value, "role": subject.get("role")}
        )
        return effect
