"""
Unit and Integration Tests for Milestone 57: Enterprise Governance, Policy Enforcer & Compliance Audit Trail Engine.
Tag: v2.1.0-policy-compliance-engine
"""
import time
from sarathi.governance import (
    PolicyEffect, PolicyRule, PolicyEngine,
    AuditEntry, AuditLogger,
    PIIRedactor, GovernanceManager
)

def test_policy_engine_abac():
    engine = PolicyEngine(default_effect=PolicyEffect.DENY)
    rule_admin = PolicyRule(rule_id="r1", subject_role="admin", action="write", effect=PolicyEffect.ALLOW)
    rule_tenant = PolicyRule(rule_id="r2", subject_role="user", action="read", conditions={"tenant_id": "tenant_1"}, effect=PolicyEffect.ALLOW)

    engine.add_rule(rule_admin)
    engine.add_rule(rule_tenant)

    # Admin write -> ALLOW
    assert engine.evaluate({"role": "admin"}, "write", {}) == PolicyEffect.ALLOW
    # User read with matching tenant -> ALLOW
    assert engine.evaluate({"role": "user", "tenant_id": "tenant_1"}, "read", {}) == PolicyEffect.ALLOW
    # User write -> DENY (default)
    assert engine.evaluate({"role": "user"}, "write", {}) == PolicyEffect.DENY

def test_tamper_evident_audit_log_hash_chain():
    logger = AuditLogger()

    logger.log("e1", actor="user1", action="CREATE_DOC", resource_id="doc100")
    logger.log("e2", actor="user2", action="UPDATE_DOC", resource_id="doc100")
    logger.log("e3", actor="admin", action="DELETE_DOC", resource_id="doc100")

    assert len(logger.chain) == 3
    assert logger.verify_integrity()

    # Attempt tamper with entry e2 metadata
    logger.chain[1].metadata["hacked"] = True
    assert not logger.verify_integrity()  # Hash chain verification catches tampering

def test_pii_redaction_interceptor():
    redactor = PIIRedactor()

    text = "Contact Alice at alice@example.com or call +1-555-0199 with SSN 123-45-6789."
    cleaned_text = redactor.redact_text(text)

    assert "alice@example.com" not in cleaned_text
    assert "123-45-6789" not in cleaned_text
    assert "[REDACTED]" in cleaned_text

    data_dict = {
        "user_email": "bob@domain.org",
        "nested": {"contact_phone": "555-123-4567"},
        "tags": ["normal", "card 4111-1111-1111-1111"]
    }
    cleaned_dict = redactor.redact_dict(data_dict)
    assert "bob@domain.org" not in cleaned_dict["user_email"]
    assert "[REDACTED]" in cleaned_dict["nested"]["contact_phone"]

def test_governance_manager_orchestrator():
    gov = GovernanceManager(default_policy_effect=PolicyEffect.DENY)
    gov.policy_engine.add_rule(PolicyRule("r1", subject_role="analyst", action="query", effect=PolicyEffect.ALLOW))

    res = gov.authorize_and_log(
        subject={"id": "usr_99", "role": "analyst"},
        action="query",
        resource={"id": "res_vector_idx"},
        entry_id="audit_evt_1"
    )

    assert res == PolicyEffect.ALLOW
    assert len(gov.audit_logger.chain) == 1
    assert gov.audit_logger.verify_integrity()
