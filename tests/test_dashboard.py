import unittest

class TestDashboard(unittest.TestCase):
    def test_dashboard_import(self):
        try:
            from culler.dashboard.feedback_server import app
        except ImportError as e:
            self.fail(f"Dashboard import failed: {e}")

if __name__ == '__main__':
    unittest.main()
