"""
Unit and Integration Tests for Milestone 59: Enterprise Federated Learning & Differential Privacy Engine.
Tag: v2.3.0-federated-privacy-engine
"""
import pytest
from sarathi.privacy import (
    PrivacyBudgetExhaustedError, PrivacyBudgetTracker,
    DifferentialPrivacyEngine, FederatedAggregator, PrivacyManager
)

def test_privacy_budget_tracker_exhaustion():
    tracker = PrivacyBudgetTracker(max_epsilon=2.0)
    tracker.consume(epsilon=1.0)
    assert tracker.remaining_budget()["remaining_epsilon"] == 1.0

    tracker.consume(epsilon=1.0)
    assert tracker.remaining_budget()["remaining_epsilon"] == 0.0

    try:
        tracker.consume(epsilon=0.5)
        assert False, "Should raise PrivacyBudgetExhaustedError"
    except PrivacyBudgetExhaustedError:
        assert True

def test_differential_privacy_noise():
    dp = DifferentialPrivacyEngine(PrivacyBudgetTracker(max_epsilon=10.0))
    original_vector = [10.0, 20.0, 30.0, 40.0]

    noisy_laplace = dp.add_laplace_noise(original_vector, epsilon=0.1)
    assert len(noisy_laplace) == 4

    noisy_gaussian = dp.add_gaussian_noise(original_vector, epsilon=0.1)
    assert len(noisy_gaussian) == 4

def test_federated_averaging_aggregator():
    client1 = {"weight_w1": [1.0, 2.0], "bias_b1": [0.5]}
    client2 = {"weight_w1": [3.0, 4.0], "bias_b1": [1.5]}

    aggregated = FederatedAggregator.aggregate_fedavg([client1, client2], [50, 50])

    assert aggregated["weight_w1"] == [2.0, 3.0]
    assert aggregated["bias_b1"] == [1.0]

def test_privacy_manager_anonymization():
    pm = PrivacyManager(max_epsilon=5.0)
    vec = [10.5, 20.8, -10.2]
    anonymized = pm.anonymize_vector(vec, epsilon=0.1)

    assert len(anonymized) == 3
    assert pm.budget_tracker.consumed_epsilon == 0.1
