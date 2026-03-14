from api.functions import Functions
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.progress import track

import questionary


class GUI:
    def __init__(self, version):
        self.version = version
        self.funcs = Functions()
        self.console = Console()

    def print(self, msg):
        self.console.print(msg)

    def pause(self, msg):
        input(msg)

    def warning(self, msg):
        self.console.print(f"[yellow]{msg}[/yellow]")

    def simpleInput(self, msg):
        return questionary.text(msg).ask()

    def progress(self, func):
        pass

    def chooseFromArr(self, msg="> ", arr=[], titleToGet="", returnIdx=False,
                      hasBack=True):
        # TODO: Support multiple pages
        try:
            choices = []
            if hasBack:
                choices.append(questionary.Choice(title="Back", value=-1))

            for i, item in enumerate(arr):
                if isinstance(item, dict):
                    display = item.get(titleToGet)
                    choices.append(questionary.Choice(title=display, value=i))
                else:
                    choices.append(item)

            choice = questionary.select(
                    message=msg, choices=choices,
                    use_jk_keys=False, use_shortcuts=True
            ).ask()

            if returnIdx:
                return choice if choice != -1 else None

            return arr[choice] if choice != -1 else None
        except Exception:
            input(self.console.print_exception())

    def printBanner(self):
        self.console.clear()
        text = "[grey23]**********************[/grey23]\n"
        text += f"  hi-cli | [italic red]{self.version}[/italic red]\n"
        text += "[grey23]**********************[/grey23]"

        self.console.print(text)

    def printConfirm(self, msg):
        return questionary.confirm(msg).ask()

    def printXXMenu(self, actions=[], menuName="", hasBack=True, msg="> "):
        self.printBanner()
        self.console.print(f"-- [b]{menuName}[/b] --")

        if len(actions) == 0:
            # Simple question instead of list choice
            r = self.simpleInput(msg)
        else:
            r = self.chooseFromArr(arr=actions, titleToGet="title",
                                   returnIdx=True, hasBack=hasBack)
        return r

    def printAnimeInfo(self, info):
        title = "--[grey23]Anime Info[/grey23]--\n"
        sub = "--[grey23]End info[/grey23]--\n"

        text = ""
        for val, key in info.items():
            if val == "episodes" or (val == "next ep" and
                                     isinstance(key, dict)):
                continue

            text += f"[green3]{val}[/green3]: [bright_red]{key}[/bright_red]\n"
        self.console.print(Panel(text, title=title, subtitle=sub))

    def printSchedule(self, schedule):
        table = Table(title="Today's schedule")

        table.add_column("Title", style="cyan")
        table.add_column("Release time", style="green")
        table.add_column("Episode to release", style="yellow")

        for obj in schedule:
            table.add_row(
                    obj.get("name"),
                    obj.get("time"),
                    obj.get("episode")
            )
        self.console.print(table)
