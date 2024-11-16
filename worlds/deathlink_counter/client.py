import asyncio
import time
import urllib.parse
from asyncio import Task
from typing import Optional, Set, Dict, Any

from CommonClient import CommonContext, ClientCommandProcessor, get_base_parser, gui_enabled, logger


class DeathLinkCounterCommandProcessor(ClientCommandProcessor):
    ctx: "DeathLinkCounterContext"

    def _cmd_death_link_count(self):
        self.output(f"Death Link count: {self.ctx.death_link_count}")

    def _cmd_client_data(self):
        """Show client data, for debugging"""
        attr_list = [
            "death_link_count",
            "data_storage",
            "client_index",
            "server_anchor_time",
            "client_anchor_time_measurement",
            "last_death_link_received",
            "last_death_link_timed",
        ]
        for attr in attr_list:
            self.output("obj.%s = %r" % (attr, getattr(self.ctx, attr)))


class DeathLinkCounterContext(CommonContext):
    command_processor = DeathLinkCounterCommandProcessor
    tags: Set[str] = {"AP", "Tracker", "DeathLink"}
    game = ""
    items_handling = 0b111  # item handling for client commands
    want_slot_data: bool = False

    process_death_links_task: Optional[Task] = None
    death_link_event = asyncio.Event()
    sleep_task_for_process_death_links: Optional[Task] = None

    death_link_count: int = 0
    data_storage: Dict[str, Any] = {}
    client_index: Optional[int] = None
    server_anchor_time: Optional[float] = None
    client_anchor_time_measurement: Optional[float] = None
    last_death_link_received: Optional[float] = None
    last_death_link_timed: Optional[float] = None

    def __init__(self, server_address, password):
        super(DeathLinkCounterContext, self).__init__(server_address, password)
        self.command_processor(self)

    def calc_current_time(self) -> Optional[float]:
        if self.server_anchor_time is None or self.client_anchor_time_measurement is None:
            return None
        return self.server_anchor_time + time.monotonic() - self.client_anchor_time_measurement

    def start_process_death_links_task(self):
        if self.process_death_links_task is None or self.process_death_links_task.done():
            self.process_death_links_task = asyncio.create_task(process_death_links(self))

    async def server_auth(self, password_requested: bool = False):
        if password_requested and not self.password:
            await super(DeathLinkCounterContext, self).server_auth(password_requested)
        await self.get_username()
        await self.send_connect()

    def on_deathlink(self, data: Dict[str, Any]) -> None:
        time_received = data.get("time", None)
        if type(time_received) is not float:
            logger.warn(
                f"""Received malformed death link {{ time:{
                time_received
                }, source:{
                data.get("source", "")
                }, text: {
                data.get("cause", "")
                } }}, discarding it.""",
            )
        else:
            self.death_link_count += 1
            self.last_death_link_received = time_received
            killer = data.get("source", "")
            if killer:
                logger.info(f"Killed by {killer}, because of \"{data.get('cause', '')}\"")
            else:
                logger.info(f"Killed because of \"{data.get('cause', '')}\"")
            self.death_link_event.set()
            self.start_process_death_links_task()
            self.last_death_link_timed = self.calc_current_time()

    async def send_death(self, death_text: str = ""):
        """Override the function to make sure this client doesn't send deaths erroneously"""
        pass

    def on_package(self, cmd: str, args: dict):
        if cmd == "RoomInfo":
            time_measurement = time.monotonic()
            server_time = args.get("time", None)
            if server_time is not None:
                self.server_anchor_time = server_time
                self.client_anchor_time_measurement = time_measurement


async def process_death_links(ctx: DeathLinkCounterContext, delay=5.0):
    while not ctx.exit_event.is_set():
        if not ctx.death_link_event.is_set():
            break
        ctx.sleep_task_for_process_death_links = asyncio.create_task(asyncio.sleep(delay))
        try:
            await ctx.sleep_task_for_process_death_links
        except asyncio.CancelledError:
            raise
        finally:
            if not ctx.death_link_event.is_set():
                break
            logger.info(f"Death Link count: {ctx.death_link_count}")
            ctx.death_link_event.clear()


async def main(args):
    ctx = DeathLinkCounterContext(args.connect, args.password)
    ctx.auth = args.name

    if gui_enabled:
        ctx.run_gui()
    ctx.run_cli()

    await ctx.exit_event.wait()
    if ctx.sleep_task_for_process_death_links is not None:
        ctx.sleep_task_for_process_death_links.cancel()
    if ctx.process_death_links_task is not None:
        await ctx.process_death_links_task
    await ctx.shutdown()


def launch():
    import colorama

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

    # use colorama to display colored text highlighting on windows
    colorama.init()

    asyncio.run(main(args))
    colorama.deinit()


if __name__ == "__main__":
    launch()
