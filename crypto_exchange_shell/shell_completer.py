try:
    import readline
except ImportError: #Window systems don't have GNU readline
    import pyreadline.windows_readline as readline
    readline.rl.mode.show_all_if_ambiguous = "on"

class ShellCompleter:
    def __init__(self):
        readline.parse_and_bind("tab: complete")
        readline.set_completer(self.generate_suggestions)
        readline.set_completer_delims(' \t\n`~!@#$%^&*()=+[{]}\\|;:\'",<>/?')

    def generate_suggestions(self, text, state):
        if readline.get_begidx() == 0:
            # First word on buffer, generate names
            return self.generate_commands(text, state)
        else:
            # This may be a parameter to our current command
            return self.generate_parameters(text, state)

    def generate_commands(self, text, state):
        pass

    def generate_parameters(self, text, state):
        pass

