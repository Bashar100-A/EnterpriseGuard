import unittest
import adie

class TestADIEPackage(unittest.TestCase):
    
    def test_package_exports(self):
        self.assertTrue(hasattr(adie, "ADIEIntegration"))
        self.assertTrue(hasattr(adie, "ADIEOrchestrator"))
        self.assertTrue(hasattr(adie, "__version__"))

    def test_integration_module_loaded(self):
        self.assertIsNotNone(adie.INTEGRATION_MODULE_NAME)

    def test_orchestrator_module_loaded(self):
        self.assertIsNotNone(adie.ORCHESTRATOR_MODULE_NAME)

if __name__ == "__main__":
    unittest.main()
