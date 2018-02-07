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

    def test_appropriate_float_format_string(self):
        self.assertEqual(
            '100.000',
            utils.make_appropriate_float_format_string(100.0).format(100.0)
        )
        self.assertEqual(
            '10.0000',
            utils.make_appropriate_float_format_string(10.0).format(10.0)
        )
        self.assertEqual(
            '1.00000',
            utils.make_appropriate_float_format_string(1.0).format(1.0)
        )
        self.assertEqual(
            '0.01000',
            utils.make_appropriate_float_format_string(0.01).format(0.01)
        )
        self.assertEqual(
            '0.00100',
            utils.make_appropriate_float_format_string(0.001).format(0.001)
        )
        self.assertEqual(
            '0.000100',
            utils.make_appropriate_float_format_string(0.00010).format(0.00010)
        )
        self.assertEqual(
            '0.0000100',
            utils.make_appropriate_float_format_string(0.00001).format(0.00001)
        )
        self.assertEqual(
            '0.00000100',
            utils.make_appropriate_float_format_string(0.000001).format(0.000001)
        )
