import unittest
import crypto_exchange_shell.utils as utils

class TestUtils(unittest.TestCase):
    def test_rounding_by_whole_numbers(self):
        self.assertEqual(1.0, utils.round_order_value(1.0, 1.0))
        self.assertEqual(2.0, utils.round_order_value(1.0, 2.0))
        self.assertEqual(2.0, utils.round_order_value(1.0, 2.5))
        self.assertEqual(0.0, utils.round_order_value(1.0, 0.5))
        self.assertEqual(10.0, utils.round_order_value(10.0, 16.0))
        self.assertEqual(100.0, utils.round_order_value(100.0, 115.0))

    def test_rounding_by_decimals(self):
        self.assertEqual(0.05, utils.round_order_value(0.001, 0.05056087))
        self.assertEqual(0.051, utils.round_order_value(0.001, 0.051))
        self.assertEqual(0.2, utils.round_order_value(0.001, 0.2001))
        self.assertEqual(0.1, utils.round_order_value(0.1, 0.11))
        self.assertEqual(0.5, utils.round_order_value(0.1, 0.56))
        self.assertEqual(1.5, utils.round_order_value(0.1, 1.56))
        self.assertEqual(1.56, utils.round_order_value(0.01, 1.56666))
