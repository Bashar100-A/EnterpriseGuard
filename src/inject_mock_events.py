"""
EnterpriseGuard - Mock Event Injector (Fixed - uses DashboardAPI)
"""

import sys
import time
import random

from enterpriseguard.api.dashboard_api import DashboardAPI
from enterpriseguard.intelligence.dashboard_service import DashboardService
from enterpriseguard.intelligence.reporting_service import ReportingService
from enterpriseguard.intelligence.decision_orchestrator import DecisionOrchestrator
from enterpriseguard.intelligence.detection_service import DetectionService
from enterpriseguard.intelligence.detector import Detector
from enterpriseguard.intelligence.models import EnterpriseGuardModel


def get_model():
    model = EnterpriseGuardModel(auto_load=True)
    if not model.trained:
        print("Training model...")
        samples = []
        labels = []
        for _ in range(5):
            samples.append({
                "request_frequency": 0.1,
                "failure_ratio": 0.05,
                "unique_source_count": 0.1,
                "unique_user_count": 0.1,
                "failed_attempts": 1.0,
                "anomaly_score": 0.05,
                "outbound_data_volume": 0.1
            })
            labels.append(0)
        for _ in range(5):
            samples.append({
                "request_frequency": 0.9,
                "failure_ratio": 0.85,
                "unique_source_count": 0.8,
                "unique_user_count": 0.85,
                "failed_attempts": 12.0,
                "anomaly_score": 0.9,
                "outbound_data_volume": 0.8
            })
            labels.append(1)
        model.train(samples, labels, persist=True)
        print("Model trained.")
    return model


def generate_event(index):
    if index % 2 == 0:
        features = {
            "request_frequency": 0.1,
            "failure_ratio": 0.05,
            "unique_source_count": 0.1,
            "unique_user_count": 0.1,
            "failed_attempts": 1.0,
            "anomaly_score": 0.05,
            "outbound_data_volume": 0.1
        }
    else:
        features = {
            "request_frequency": 0.9,
            "failure_ratio": 0.85,
            "unique_source_count": 0.8,
            "unique_user_count": 0.85,
            "failed_attempts": 12.0,
            "anomaly_score": 0.9,
            "outbound_data_volume": 0.8
        }
    features.update({
        "source": f"192.168.1.{random.randint(1, 255)}",
        "user": f"user_{random.randint(1, 50)}",
        "success": random.random() > 0.35,
        "request_id": f"EVT-{int(time.time())}-{index}",
    })
    return features


def main():
    print("=" * 60)
    print("EnterpriseGuard - Mock Event Injector (Fixed)")
    print("Safe test environment - no real security actions")
    print("=" * 60)

    # Build the exact same components as the dashboard
    model = get_model()
    detector = Detector(model)
    detection_service = DetectionService(detector)
    orchestrator = DecisionOrchestrator()
    reporting = ReportingService()
    
    print("Processing events...")
    
    for i in range(1, 21):
        event = generate_event(i)
        result = detection_service.analyze([event])
        orch_result = orchestrator.handle(result)
        reporting.record(orch_result)
        
        status = "THREAT" if result.decision in ("ALERT", "ESCALATE") else "SAFE"
        print(f"   Event {i:02d}: {status} | decision: {result.decision} | queued: {orch_result.queued}")
        time.sleep(0.05)

    # Now we need to make these available to the dashboard
    # The dashboard uses its own instances, so we save to a shared location
    import pickle
    with open("reporting_state.pkl", "wb") as f:
        pickle.dump(reporting, f)
    
    print(f"\n📊 Summary:")
    summary = reporting.get_summary()
    print(f"   Total records: {summary['total_records']}")
    print(f"   Alerts: {summary['alert_count']}")
    print(f"   Escalations: {summary['escalation_count']}")

    print("\n" + "=" * 60)
    print("✅ Events injected successfully!")
    print("📌 Now restart Streamlit to see the data.")
    print("   (Press Ctrl+C in Streamlit window, then run again)")
    print("=" * 60)


if __name__ == "__main__":
    main()