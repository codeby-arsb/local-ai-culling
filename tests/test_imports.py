import unittest

class TestImports(unittest.TestCase):
    def test_core_imports(self):
        try:
            from culler.engine.pipeline import Pipeline
            from culler.engine.config import AppConfig
            from culler.ai.classification import classify_records
        except ImportError as e:
            self.fail(f"Import failed: {e}")

if __name__ == '__main__':
    unittest.main()
