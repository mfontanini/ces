import unittest
from crypto_exchange_shell.parameter_parser import *
from crypto_exchange_shell.exceptions import *

class TestParameterParser(unittest.TestCase):
    def extract_exception(self, functor):
        try:
            functor()
            return None
        except Exception as ex:
            return ex

    def test_parse_positional_int(self):
        parser = ParameterParser([
            PositionalParameter(
                'value',
                type_parser=TypedTypeParser.make_parser(int),
                required=True
            )
        ])
        result = parser.parse('15')
        self.assertEqual(15, result['value'])
        self.assertRaises(MissingParameterException, lambda: parser.parse(''))

    def test_parse_not_required(self):
        parser = ParameterParser([
            PositionalParameter(
                'value',
                type_parser=TypedTypeParser.make_parser(int),
                required=False
            )
        ])
        self.assertEqual(len(parser.parse('')), 0)

    def test_parse_positional_float(self):
        parser = ParameterParser([
            PositionalParameter(
                'value',
                parameter_type=float,
                required=True
            )
        ])
        result = parser.parse('3.14')
        self.assertEqual(3.14, result['value'])

    def test_parse_positional_str(self):
        parser = ParameterParser([
            PositionalParameter(
                'value',
                parameter_type=str,
                required=True
            )
        ])
        result = parser.parse('hello')
        self.assertEqual('hello', result['value'])

    def test_parse_named_int(self):
        parser = ParameterParser([
            NamedParameter(
                'value',
                parameter_type=int,
                required=True
            )
        ])
        result = parser.parse('value 100')
        self.assertEqual(100, result['value'])

    def test_parse_swallo_input(self):
        parser = ParameterParser([
            SwallowInputParameter(
                'value',
                required=True
            )
        ])
        result = parser.parse('value hello world')
        self.assertEqual('hello world', result['value'])

    def test_const(self):
        parser = ParameterParser([
            ConstParameter(
                'value',
                required=True,
                keyword='heh'
            )
        ])
        result = parser.parse('heh')
        self.assertTrue(result['value'])        

    def test_parse_group(self):
        parser = ParameterParser([
            PositionalParameter('value1', parameter_type=str),
            PositionalParameter('value2', parameter_type=int)
        ])
        result = parser.parse('hello 15')
        self.assertEqual('hello', result['value1'])
        self.assertEqual(15, result['value2'])

    def test_parse_group_named(self):
        parser = ParameterParser([
            NamedParameter('value1', parameter_type=int),
            NamedParameter('value2', parameter_type=str, required=True),
        ])
        result1 = parser.parse('value1 100 value2 hello')
        result2 = parser.parse('value2 hello value1 100')
        self.assertEqual(result1, result2)
        self.assertEqual(100, result1['value1'])
        self.assertEqual('hello', result1['value2'])
        self.assertRaises(MissingParameterException, lambda: parser.parse('value1 100'))

    def test_parse_choice(self):
        parser = ParameterParser([
            ParameterChoice([
                NamedParameter('value1', parameter_type=int),
                NamedParameter('value2', parameter_type=str),
            ])
        ])
        self.assertEqual(100, parser.parse('value1 100')['value1'])
        self.assertEqual('hello', parser.parse('value2 hello')['value2'])

    def test_parse_choice_groups(self):
        parser = ParameterParser([
            ParameterChoice([
                ParameterGroup([
                    NamedParameter('value1', parameter_type=str),
                    NamedParameter('value2', parameter_type=str, required=False),
                ]),
                ParameterGroup([
                    NamedParameter('value3', parameter_type=str),
                    NamedParameter('value4', parameter_type=str, required=False),
                ])
            ])
        ])
        self.assertEqual('hello', parser.parse('value1 hello')['value1'])
        self.assertEqual('hello', parser.parse('value3 hello')['value3'])
        # Try mixing choices, this should throw
        self.assertRaises(ParameterParsingException, lambda: parser.parse('value1 hello value3 bye'))

    def test_complex1(self):
        parser = ParameterParser([
            ParameterChoice([
                ParameterGroup([
                    ConstParameter('action', keyword='list'),
                    PositionalParameter('currency', parameter_type=str, required=False)
                ]),
                ParameterGroup([
                    ConstParameter('action', keyword='add'),
                    PositionalParameter('currency', parameter_type=str),
                    NamedParameter('name', parameter_type=str),
                    NamedParameter('address', parameter_type=str)
                ]),
                ParameterGroup([
                    ConstParameter('action', keyword='remove'),
                    NamedParameter('name', parameter_type=str),
                ])
            ])
        ])
        self.assertEqual(
            parser.parse('list'),
            { 'action' : 'list' }
        )
        self.assertEqual(
            parser.parse('list XLM'),
            { 'action' : 'list', 'currency' : 'XLM' }
        )
        self.assertEqual(
            parser.parse('add XLM name test address 123'),
            { 'action' : 'add', 'currency' : 'XLM', 'name' : 'test', 'address' : '123' }
        )
        self.assertEqual(
            parser.parse('remove name test'),
            { 'action' : 'remove', 'name' : 'test' }
        )
        # Failure cases
        self.assertRaises(MissingParametersException, lambda: parser.parse('add XLM'))

        self.assertRaises(MissingParameterException, lambda: parser.parse('add XLM name bleh'))
        self.assertEqual(
            self.extract_exception(lambda: parser.parse('add XLM name bleh')).parameter,
            'address'
        )

        self.assertRaises(ParameterParsingException, lambda: parser.parse('add XLM name'))
        self.assertEqual(
            self.extract_exception(lambda: parser.parse('add XLM name')).line,
            'name'
        )

if __name__ == "__main__":
    unittest.main()
