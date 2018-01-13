try:
    import readline
except ImportError: #Window systems don't have GNU readline
    import pyreadline.windows_readline as readline
    readline.rl.mode.show_all_if_ambiguous = "on"

class ShellCompleter:
    def __init__(self, core):
        self._core = core
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.generate_suggestions)
        readline.set_completer_delims(' \t\n`~!@#$%^&*()=+[{]}\\|;:\'",<>/?')

    def generate_suggestions(self, text, state):
        try:
            if readline.get_begidx() == 0:
                # First word on buffer, generate names
                return self._generate_commands(text, state)
            else:
                # This may be a parameter to our current command
                return self._generate_parameters(text, state)
        except Exception as ex:
            print 'Error: {0}'.format(ex)
            raise ex

    def _generate_commands(self, text, state):
        if state == 0:
            self._setup_completion(text, self._core.cmd_manager.get_command_names())
        return self._get_completion(text, state)

    def _generate_parameters(self, text, state):
        if state == 0:
            line = readline.get_line_buffer()
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
