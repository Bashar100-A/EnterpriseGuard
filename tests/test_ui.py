import sys
import unittest
from PyQt6.QtWidgets import QApplication, QTabWidget, QPushButton, QTextEdit, QLabel
from PyQt6.QtTest import QTest
from PyQt6.QtCore import Qt

from enterpriseguard.ui.app import EnterpriseGuardUI

# إنشاء كائن QApplication موحد لبيئة الاختبارات
app = QApplication.instance() or QApplication(sys.argv)


class DummyDashboardService:
    def refresh(self):
        return {
            "metrics": {
                "total_events": 42,
                "alert_count": 3,
                "escalation_count": 1,
                "threat_rate": 0.07,
            },
            "health": {
                "status": "HEALTHY"
            },
            "alerts": [
                {"operation_id": "op-101", "status": "FLAGGED", "decision": "ISOLATE"}
            ],
            "escalations": []
        }

    def get_status(self):
        return "HEALTHY"

    def get_telemetry_summary(self):
        return self.refresh()

class DummyOrchestrator:
    def __init__(self):
        self._state_provider = object()
        self._prediction_provider = object()
        self._policy_provider = object()
        self._decision_provider = object()
        self._checkpoint_provider = None
        self._playbook_provider = None
        self._rollback_provider = None

    def run_integrity_check(self):
        return {"status": "PASS", "errors": [], "warnings": []}


class TestEnterpriseGuardUI(unittest.TestCase):
    def setUp(self):
        self.dashboard_service = DummyDashboardService()
        self.orchestrator = DummyOrchestrator()
        self.ui = EnterpriseGuardUI(
            dashboard_service=self.dashboard_service,
            orchestrator=self.orchestrator
        )

    def tearDown(self):
        self.ui.close()

    def test_tab_widget_structure_and_navigation(self):
        """اختبار وجود اللوحات الثلاث والتنقل بينها"""
        tab_widget = self.ui.findChild(QTabWidget)
        self.assertIsNotNone(tab_widget, "QTabWidget غير موجود في الواجهة")
        self.assertEqual(tab_widget.count(), 3)

        # التحقق من أسماء التبويبات
        tab_names = [tab_widget.tabText(i) for i in range(tab_widget.count())]
        self.assertIn("Dashboard", tab_names)
        self.assertIn("Integrity", tab_names)
        self.assertIn("Policy", tab_names)

        # اختبار تبديل التبويب برمجياً
        tab_widget.setCurrentIndex(1)
        self.assertEqual(tab_widget.currentIndex(), 1)
        tab_widget.setCurrentIndex(2)
        self.assertEqual(tab_widget.currentIndex(), 2)

    def test_dashboard_view_refresh_button(self):
        """اختبار زر تحديث القياسات في لوحة التحكم"""
        tab_widget = self.ui.findChild(QTabWidget)
        dashboard_view = tab_widget.widget(0)
        
        refresh_btn = dashboard_view.findChild(QPushButton)
        self.assertIsNotNone(refresh_btn, "لم يتم العثور على زر التحديث في DashboardView")

        QTest.mouseClick(refresh_btn, Qt.MouseButton.LeftButton)

        # فحص كلي لكافة عناصر QLabel و QTextEdit غير حساسة لحالة الأحرف
        labels = dashboard_view.findChildren(QLabel)
        all_text = " ".join([lbl.text() for lbl in labels]).upper()
        
        self.assertIn("HEALTHY", all_text, f"لم يتم العثور على كلمة HEALTHY داخل النصوص: {all_text}")

    def test_integrity_view_run_check_button(self):
        """اختبار زر تشغيل النزاهة في لوحة Integrity"""
        tab_widget = self.ui.findChild(QTabWidget)
        integrity_view = tab_widget.widget(1)

        run_btn = integrity_view.findChild(QPushButton)
        self.assertIsNotNone(run_btn, "لم يتم العثور على زر الفحص في IntegrityView")

        # إجراء النقر
        QTest.mouseClick(run_btn, Qt.MouseButton.LeftButton)

        # التحقق من طباعة النتيجة JSON في النص
        text_edit = integrity_view.findChild(QTextEdit)
        self.assertIsNotNone(text_edit)
        self.assertIn("PASS", text_edit.toPlainText())


if __name__ == "__main__":
    unittest.main()
