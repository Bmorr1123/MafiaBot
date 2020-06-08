
class Command:
    def __init__(self, alias, args, func, desc):
        self.alias = alias
        self.args = args
        self.func = func
        if desc is None:
            desc = "This command has no description."
        self.desc = desc

    def run(self, *args):
        return self.func(*args)


commands = []
def cmd(command: callable):
    commands.append(Command(
        alias=command.__name__,
        args=command.__code__.co_varnames,
        func=command,
        desc=command.__doc__
    ))
    return command

@cmd
def help():
    """This command returns the list of commands and their function."""
    output = ""
    for index, command in enumerate(commands):
        output += f"{command.alias} - {command.desc}"
        if index != len(commands) - 1:
            output += "\n"
    return output
