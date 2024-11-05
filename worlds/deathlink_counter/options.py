from dataclasses import dataclass

from Options import Toggle, PerGameCommonOptions

class PrintDeathMessages(Toggle):
    """Sends death messages to archipelago chat"""
    display_name = "Print Death Messages"

@dataclass
class DeathLinkCounterOptions(PerGameCommonOptions):
    print_death_messages: PrintDeathMessages