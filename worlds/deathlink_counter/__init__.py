from typing import Dict, Any
from worlds.AutoWorld import World
from worlds.LauncherComponents import Component, components, Type, launch_subprocess
from .options import DeathLinkCounterOptions


def launch_client():
    from .client import launch
    import sys
    if not sys.stdout or "--nogui" not in sys.argv:
        launch_subprocess(launch, name="DeathLink Counter client")
    else:
        launch()

components.append(Component("DeathLink Counter Client", "DeathLinkCounterClient", func=launch_client, component_type=Type.CLIENT))

class DeathLinkCounterWorld(World):
    game = "DeathLink Counter"
    options_dataclass = DeathLinkCounterOptions
    options: DeathLinkCounterOptions

    item_name_to_id = {}
    location_name_to_id = {}

    def fill_slot_data(self) -> Dict[str, Any]:
        return self.options.as_dict("print_death_messages")
