import sys
import logging
from PyQt6.QtWidgets import QApplication
from enterpriseguard.ui.app import EnterpriseGuardUI

from enterpriseguard.intelligence.dashboard_service import DashboardService
from enterpriseguard.intelligence.reporting_service import ReportingService
from enterpriseguard.intelligence.decision_orchestrator import DecisionOrchestrator

from enterpriseguard.adie.orchestrator import ADIEOrchestrator
from enterpriseguard.adie.prediction import PredictionService
from enterpriseguard.adie.policy import ADIEPolicy
from enterpriseguard.adie.decision import DecisionEngine
import enterpriseguard.adie.state as state_mod

logger = logging.getLogger(__name__)

# --- محولات العقود (Adapters) لترجمة الاستدعاءات ---

class StateProviderAdapter:
    def collect(self, *args, **kwargs):
        if hasattr(state_mod, "create_initial_state"):
            return state_mod.create_initial_state()
        return {}

    def get_status(self, *args, **kwargs):
        return {"status": "HEALTHY", "source": "StateProviderAdapter"}

class DecisionProviderAdapter:
    def __init__(self, engine):
        self._engine = engine

    def decide(self, *args, **kwargs):
        if hasattr(self._engine, "decide"):
            return self._engine.decide(*args, **kwargs)
        elif hasattr(self._engine, "evaluate"):
            return self._engine.evaluate(*args, **kwargs)
        return {"decision": "ALLOW", "confidence": 1.0}

def main():
    app = QApplication(sys.argv)
    
    dashboard_service = None
    orchestrator = None

    # 1. بناء الموفرات وتطبيق المحولات
    try:
        state_prov = StateProviderAdapter()
        pred_prov = PredictionService()
        pol_prov = ADIEPolicy()
        dec_prov = DecisionProviderAdapter(DecisionEngine())

        orchestrator = ADIEOrchestrator(
            state_provider=state_prov,
            prediction_provider=pred_prov,
            policy_provider=pol_prov,
            decision_provider=dec_prov
        )
    except Exception as e:
        logger.error(f"Failed to initialize ADIEOrchestrator: {e}")

    # 2. تهيئة خدمة Dashboard
    try:
        dashboard_service = DashboardService(
            reporting_service=ReportingService(),
            decision_orchestrator=DecisionOrchestrator()
        )
    except Exception as e:
        logger.error(f"Failed to initialize DashboardService: {e}")

    # 3. تشغيل الواجهة
    window = EnterpriseGuardUI(
        dashboard_service=dashboard_service,
        orchestrator=orchestrator
    )
    window.show()
    sys.exit(app.exec())

if __name__ == "__main__":
    main()
