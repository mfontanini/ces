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

try:
    import readline
except ImportError: #Window systems don't have GNU readline
    import pyreadline.windows_readline as readline
    readline.rl.mode.show_all_if_ambiguous = "on"

class ShellCompleter:
    def __init__(self, core):
        self._core = core
        self._last_state = None
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.generate_suggestions)
        readline.set_completer_delims(' \t\n`~!@#$%^&*()=+[{]}\\|;:\'",<>/?')

    def generate_suggestions(self, text, state):
        if self._last_state is not None:
            if self._last_state['text'] == text and \
               self._last_state['index'] == readline.get_begidx() and \
               self._last_state['state'] == state:
               return self._last_state['output']
        try:
            if readline.get_begidx() == 0:
                # First word on buffer, generate names
                output = self._generate_commands(text, state)
            else:
                # This may be a parameter to our current command
                output = self._generate_parameters(text, state)
        except Exception as ex:
            raise ex
        self._last_state = {
            'text' : text,
            'index' : readline.get_begidx(),
            'state' : state,
            'output' : output
        }
        return output

    def _generate_commands(self, text, state):
        if state == 0:
            self._setup_completion(text, self._core.cmd_manager.get_command_names())
        return self._get_completion(text, state)

    def _generate_parameters(self, text, state):
        if state == 0:
            line = readline.get_line_buffer().lstrip()
            tokens = line[:readline.get_endidx()].split(' ')
            try:
                command = self._core.cmd_manager.get_command(tokens[0])
            except:
                return None
            tokens = filter(lambda i: len(i) > 0, tokens)
            # Remove the last one as it's a partial match
            if len(tokens) > 0 and line[-1] != ' ':
                tokens.pop()
            self._setup_completion(text, command.generate_parameters(self._core, tokens[1:]))
        return self._get_completion(text, state)

    def _setup_completion(self, text, options):
        self._available = []
        for option in options:
            if option.startswith(text):
                self._available.append(option)
        self._available.sort()
        self._current_index = 0

    def _get_completion(self, text, state):
        if self._current_index == len(self._available):
            return None
        else:
            current_match = self._available[self._current_index]
            self._current_index += 1
            return '{0} '.format(current_match)
