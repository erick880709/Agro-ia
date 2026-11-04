import unittest

from calculator import total


class CalculatorTests(unittest.TestCase):
    def test_adds_tax(self):
        self.assertAlmostEqual(total(100, 0.19), 119)


if __name__ == '__main__':
    unittest.main()
