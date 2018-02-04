# Copyright (c) 2018, Matias Fontanini
# All rights reserved.

# Redistribution and use in source and binary forms, with or without
# modification, are permitted provided that the following conditions are met:

# 1. Redistributions of source code must retain the above copyright notice, this
#    list of conditions and the following disclaimer.
# 2. Redistributions in binary form must reproduce the above copyright notice,
#    this list of conditions and the following disclaimer in the documentation
#    and/or other materials provided with the distribution.

# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND
# ANY EXPRESS OR IMPLIED WARRANTIES, INCLUDING, BUT NOT LIMITED TO, THE IMPLIED
# WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR
# ANY DIRECT, INDIRECT, INCIDENTAL, SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES
# (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR SERVICES;
# LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND
# ON ANY THEORY OF LIABILITY, WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT
# (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE OF THIS
# SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.

# The views and conclusions contained in the software and documentation are those
# of the authors and should not be interpreted as representing official policies,
# either expressed or implied, of the FreeBSD Project.

import itertools
from exceptions import *

class Match:
    def __init__(self, name, value):
        self.name = name
        self.value = value

class BaseTypeParser:
    def __init__(self, type_name):
        self.type_name = type_name

class TypedTypeParser(BaseTypeParser):
    @classmethod
    def make_parser(cls, type_class, **kwargs):
        return TypedTypeParser(type_class.__name__, type_class)

    def __init__(self, type_name, type_class):
        BaseTypeParser.__init__(self, type_name)
        self.type_class = type_class

    def parse(self, name, value):
        try:
            return self.type_class(value)
        except Exception as ex:
            raise InvalidParameterTypeException(name, self.type_name)

class BaseParameter:
    def __init__(self):
        pass

    def extract_token(self, line):
        tokens = line.split(' ')
        if len(tokens) == 0 or len(tokens[0]) == 0:
            return None
        return tokens[0]

    def skip_token(self, token, line):
        return line[len(token):]

    def parameters_missing(self, existing_parameters):
        return []

    def parameters_set(self, existing_parameters):
        return []

    def can_be_skipped(self):
        return True

    def is_set(self, existing_parameters):
        return False

    def is_fulfilled(self, existing_parameters):
        return True

class SingleParameter(BaseParameter):
    def __init__(self, name, required):
        BaseParameter.__init__(self)
        self.name = name
        self.required = required

    def parameters_missing(self, existing_parameters):
        return [ self.name ] if self.required and self.name not in existing_parameters else []

    def parameters_set(self, existing_parameters):
        return [ self.name ] if self.is_set(existing_parameters) else []

    def __repr__(self):
        return 'SingleParameter({0})'.format(self.name)

    def is_set(self, existing_parameters):
        return self.name in existing_parameters

    def is_fulfilled(self, existing_parameters):
        return not self.required or self.is_set(existing_parameters)

class TypedSingleParameter(SingleParameter):
    def __init__(self, name, parameter_type=None, type_parser=None, required=True):
        SingleParameter.__init__(self, name, required)
        if parameter_type is None and type_parser is None:
            raise Exception('TypedSingleParameter requires a type/parser')
        self.type_parser = type_parser or TypedTypeParser.make_parser(parameter_type)

class PositionalParameter(TypedSingleParameter):
    def __init__(self, name, **kwargs):
        TypedSingleParameter.__init__(self, name, **kwargs)

    def match(self, line, existing_parameters):
        raw_token = self.extract_token(line)
        if raw_token is None:
            return (None, line)
        parsed_token = self.type_parser.parse(self.name, raw_token)
        return (Match(self.name, parsed_token), self.skip_token(raw_token, line))

    def can_be_skipped(self):
        return not self.required

    def __repr__(self):
        return 'PositionalParameter({0})'.format(self.name)

class NamedParameter(TypedSingleParameter):
    def __init__(self, name, **kwargs):
        TypedSingleParameter.__init__(self, name, **kwargs)

    def extract_name_token(self, line):
        return self.extract_token(line)

    def extract_value_token(self, line):
        return self.extract_token(line)    

    def match(self, line, existing_parameters):
        name_token = self.extract_name_token(line)
        if name_token is None or name_token != self.name:
            return (None, line)
        raw_token = self.extract_value_token(line[len(name_token):].lstrip())
        if raw_token is None:
            return (None, line)
        index = line.index(raw_token, len(name_token))
        parsed_token = self.type_parser.parse(self.name, raw_token)
        return (Match(self.name, parsed_token), line[index + len(raw_token):])

    def __repr__(self):
        return 'NamedParameter({0})'.format(self.name)

class SwallowInputParameter(NamedParameter):
    def __init__(self, name, required=True):
        NamedParameter.__init__(self, name, type_parser=TypedTypeParser.make_parser(str), 
                                required=required)

    def extract_value_token(self, line):
        return line if len(line) > 0 else None

    def __repr__(self):
        return 'SwallowInputParameter({0})'.format(self.name)

class ConstParameter(SingleParameter):
    def __init__(self, name, required=True, keyword=None, value=None):
        SingleParameter.__init__(self, name, required)
        self.keyword = keyword or name
        self.value = value if value is not None else keyword 

    def match(self, line, existing_parameters):
        token = self.extract_token(line)
        if token is None or token != self.keyword:
            return (None, line)
        return (Match(self.name, self.value), self.skip_token(token, line))

    def parameters_missing(self, existing_parameters):
        return [ self.keyword ] if self.required and not self.is_set(existing_parameters) else []

    def parameters_set(self, existing_parameters):
        return [ self.keyword ] if self.is_set(existing_parameters) else []

    def can_be_skipped(self):
        return not self.required

    def is_set(self, existing_parameters):
        return self.name in existing_parameters and existing_parameters[self.name] == self.value

    def __repr__(self):
        return 'ConstParameter({0})'.format(self.keyword)

class ParameterGroup(BaseParameter):
    def __init__(self, parameters):
        BaseParameter.__init__(self)
        self.parameters = parameters

    def match(self, line, existing_parameters):
        for parameter in self.parameters:
            if parameter.is_set(existing_parameters):
                continue
            (match, parsed_line) = parameter.match(line, existing_parameters)
            if match is not None:
                return (match, parsed_line)
            if not parameter.can_be_skipped():
                return (None, line)
        return (None, line)

    def parameters_missing(self, existing_parameters):
        missing = map(lambda i: i.parameters_missing(existing_parameters), self.parameters)
        return list(itertools.chain.from_iterable(missing))

    def parameters_set(self, existing_parameters):
        output = []
        for parameter in self.parameters:
            if not parameter.can_be_skipped() and not parameter.is_set(existing_parameters):
                break
            set_ones = map(lambda i: i.parameters_set(existing_parameters), self.parameters)
            output += itertools.chain.from_iterable(set_ones)
        return output

    def is_set(self, existing_parameters):
        return all([i.is_set(existing_parameters) for i in self.parameters])

    def is_fulfilled(self, existing_parameters):
        return all([i.is_fulfilled(existing_parameters) for i in self.parameters])

    def __repr__(self):
        return 'ParameterGroup({0})'.format(self.parameters)

class ParameterChoice(BaseParameter):
    def __init__(self, choices):
        BaseParameter.__init__(self)
        self.choices = choices

    def _find_matching_choice(self, existing_parameters):
        potential_choices = []
        for choice in self.choices:
            if any(choice.parameters_set(existing_parameters)):
               potential_choices.append(choice)
        return potential_choices[0] if len(potential_choices) == 1 else None

    def match(self, line, existing_parameters):
        matching_choice = self._find_matching_choice(existing_parameters)
        if matching_choice:
            return matching_choice.match(line, existing_parameters)
        for choice in self.choices:
            result = choice.match(line, existing_parameters)
            if result[0]:
                return result
        return (None, line)

    def parameters_missing(self, existing_parameters):
        matching_choice = self._find_matching_choice(existing_parameters)
        if matching_choice:
            return matching_choice.parameters_missing(existing_parameters)
        missing = map(lambda i: i.parameters_missing(existing_parameters), self.choices)
        return list(itertools.chain.from_iterable(missing))

    def parameters_set(self, existing_parameters):
        set_ones = map(lambda i: i.parameters_set(existing_parameters), self.choices)
        return list(itertools.chain.from_iterable(set_ones))

    def is_set(self, existing_parameters):
        matched = [i.is_set(existing_parameters) for i in self.choices]
        return any(matched)

    def is_fulfilled(self, existing_parameters):
        return any([i.is_fulfilled(existing_parameters) for i in self.choices])

    def __repr__(self):
        return 'ParameterChoice({0})'.format(self.choices)

class ParameterParser:
    def __init__(self, root_parameters):
        self._root_parameter = ParameterGroup(root_parameters)

    def parse(self, line):
        output = {}
        while any(line):
            (match, line) = self._root_parameter.match(line, output)
            if match is None:
                break
            if match.name in output:
                raise DuplicateParameterException(match.name)
            output[match.name] = match.value
            line = line.lstrip()
        if any(line):
            raise ParameterParsingException(line) 
        if not self._root_parameter.is_fulfilled(output):
            missing = self._root_parameter.parameters_missing(output)
            if len(missing) == 1:
                raise MissingParameterException(missing[0])
            else:
                raise MissingParametersException()
        return output
