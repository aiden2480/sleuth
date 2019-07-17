from asyncio import run, get_event_loop
from sys import argv
from aiohttp import ClientSession


async def send_one(msg):
    async with ClientSession(loop=get_event_loop()) as session:
        async with session.ws_connect("http://localhost:8080/CLI/ws/") as ws:
            await ws.send_str(msg)


run(send_one(" ".join(argv[1:])))
