import unittest

from worker import CreditWorker


class CreditWorkerTests(unittest.TestCase):
    def test_duplicate_is_applied_once(self):
        worker = CreditWorker()
        worker.start()
        self.assertEqual(worker.handle('m-1', 10), 10)
        self.assertEqual(worker.handle('m-1', 10), 10)

    def test_requires_running_lifecycle(self):
        worker = CreditWorker()
        with self.assertRaises(RuntimeError):
            worker.handle('m-1', 10)
        worker.start()
        worker.stop()
        with self.assertRaises(RuntimeError):
            worker.handle('m-1', 10)


if __name__ == '__main__':
    unittest.main()
