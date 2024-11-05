import asyncio
import typing
import urllib.parse
from CommonClient import CommonContext, ClientCommandProcessor, get_base_parser, gui_enabled


class DeathLinkCounterCommandProcessor(ClientCommandProcessor):
    ctx: "DeathLinkCounterContext"

    def _cmd_test(self):
        self.output("Test Successful")

class DeathLinkCounterContext(CommonContext):
    command_processor = DeathLinkCounterCommandProcessor
    tags: typing.Set[str] = {"AP", "DeathLink"}
    game = "DeathLink Counter"
    items_handling = 0b000  # no item handling
    want_slot_data: bool = True

    def __init__(self, server_address, password):
        super(DeathLinkCounterContext, self).__init__(server_address, password)
        self.command_processor(self)

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(DeathLinkCounterContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_package(self, cmd: str, args: dict):
        pass

async def main(args):
    ctx = DeathLinkCounterContext(args.connect, args.password)
    ctx.auth = args.name

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    await ctx.shutdown()

def launch():
    parser = get_base_parser(description="Gameless Archipelago Client, for text interfacing.")
    parser.add_argument('--name', default=None, help="Slot Name to connect as.")
    parser.add_argument("url", nargs="?", help="Archipelago connection url")
    args = parser.parse_args()

    if args.url:
        url = urllib.parse.urlparse(args.url)
        args.connect = url.netloc
        if url.username:
            args.name = urllib.parse.unquote(url.username)
        if url.password:
            args.password = urllib.parse.unquote(url.password)

    asyncio.run(main(args))


if __name__ == "__main__":
    launch()