import unittest

from orders import to_payload


class PayloadTest(unittest.TestCase):
    def test_payload_has_account(self):
        self.assertEqual(to_payload("o1", "a1", ["1.00"])["account_id"], "a1")


if __name__ == "__main__":
    unittest.main()
