from aiohttp import WSMsgType, web
from aiohttp_jinja2 import template, setup as jinja2_setup
from argparse import ArgumentParser
from asyncio import create_task, wait
from datetime import datetime as dt
from emoji import emojize, demojize
from helpers import Database, MessageClient
from jinja2 import FileSystemLoader
from logging import Formatter, FileHandler, getLogger
from multiprocessing import Process
from os import environ
from secrets import token_urlsafe as gen_token

# Setup
routes = web.RouteTableDef()
websockets = set()
history = list()

# Create app
app = web.Application()
app.router.add_static("/assets", "./static")
jinja2_setup(app, loader=FileSystemLoader("./templates"))

# Setup auth config
app.config = dict()
app.config["user_tokens"] = dict()
app.config["print_messages"] = True
app.config["master_token"] = gen_token()

# Setup logging
logger = getLogger("aiohttp.access")
logger.setLevel(10)
handler = FileHandler("assets/website.log", encoding="utf-8")
handler.setFormatter(Formatter("[%(asctime)s] [%(levelname)s]: %(message)s"))
logger.addHandler(handler)
logger.debug(
    f"=   SERVER STARTED   =\n\tMaster access token: \"{app.config['master_token']}\""
)
app.logger = logger

# Parse args
parser = ArgumentParser(description="Startup options for the chat app")
parser.add_argument(
    "--noclient",
    action="store_true",
    default=False,
    help="Don't start the chat client to recieve messages in a new thread",
)
parser.add_argument("--port", type=int, default=80, help="Override the default port provided in the env")
args = parser.parse_args()


# Routes
@routes.get("/", name="index")
@template("index.jinja")
async def index(request):
    return {}


@routes.post("/")
async def login(request):
    data = await request.post()

    # Grab the required stuff
    name = data.get("user")
    _pass = data.get("pass")
    success = web.HTTPFound(request.app.router["chat"].url_for(name=name))
    fail = web.HTTPFound(request.app.router["index"].url_for())

    # Check the creds with the database
    print(f"Attempted login with creds: {data}", end=" - ")
    with Database() as db:
        if not db.is_valid_login(name, _pass):
            print("Login failed")
            return fail
        print("Login succeeded")

    # If a cookie does not exist, it creates one
    user_token = app.config["user_tokens"].get(name)
    if not user_token:
        app.config["user_tokens"][name] = gen_token()
    success.set_cookie("token", app.config["user_tokens"].get(name))

    return success


@routes.get("/{name}/", name="chat")
@template("chat.jinja")
async def chat(request):
    name = request.match_info["name"]
    auth = request.cookies.get("token")
    cauth = app.config["user_tokens"].get(name)

    # Auth checks
    if not cauth:
        # The server has not created a token because the use never logged in
        return web.HTTPFound("/")
        return web.Response(
            text="You are unauthorized. Please go back to the login page and sign in"
        )
    if cauth != auth:
        # Wrong token
        return web.HTTPFound("/")
        return web.Response(
            text="This authorization token is invalid. You will need to sign in again"
        )

    # Passed auth checks
    # return web.json_response(app.config)
    return {}


@routes.get("/{name}/ws/")
async def websocket(request):
    name = request.match_info["name"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)

    if not name == "CLI":
        await send_to_all("system", f"{name} joined the chat")

    for text in list(history):
        await ws.send_str(text)
    websockets.add(ws)

    try:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                await send_to_all(name, msg.data)
            elif msg.type == WSMsgType.ERROR:
                print("ws connection closed with exception %s" % ws.exception())
    finally:
        websockets.remove(ws)

    await send_to_all("system", f"{name} left the chat")

    return ws


@routes.get("/quit")
async def quit(request: web.Request):
    token = request.url.query.get("token")

    if token != app.config["master_token"]:
        if token == None:
            return web.Response(text="You did not provide a token")
        return web.Response(text="The provided token is invalid")

    await app.shutdown()
    await app.cleanup()
    raise KeyboardInterrupt("Web shut down")


# Send function
async def send_to_all_new(data: dict) -> None:
    text = f"{dt.now():%H:%M:%S} - {data['name']}: {data['message']}"
    if app.config["print_messages"]:
        print(text)

    history.append(text)
    if len(history) > 20:
        del history[:10]

    tasks = set()
    for ws in websockets:
        tasks.add(create_task(ws.send_json(text)))
    while tasks:
        done, tasks = await wait(tasks)


async def send_to_all(name, message):
    text = emojize(f"{dt.now():%H:%M:%S} - {name}: {message}", use_aliases=True)
    if app.config["print_messages"]:
        print(demojize(text))

    history.append(text)
    # if len(history) > 20:
    #    del history[:10]
    # ^ This deletes the history for new joining users

    tasks = set()
    for ws in websockets:
        tasks.add(create_task(ws.send_str(text)))
    while tasks:
        done, tasks = await wait(tasks)

# Finally run the damn thing
if __name__ == "__main__":
    try:
        app.add_routes(routes)
        web.run_app(app, port=environ.get("PORT", args.port))
    finally:
        logger.debug("=  SERVER SHUT DOWN  =")
