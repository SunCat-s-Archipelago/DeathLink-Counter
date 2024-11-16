from worlds.LauncherComponents import Component, components, Type, launch_subprocess


def launch_client():
    from .client import launch
    import sys
    if not sys.stdout or "--nogui" not in sys.argv:
        launch_subprocess(launch, name="DeathLink Counter client")
    else:
        launch()


components.append(Component("DeathLink Counter Client", "DeathLinkCounterClient", func=launch_client, component_type=Type.CLIENT))
