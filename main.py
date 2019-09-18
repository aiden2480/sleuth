from asyncio import create_task, wait
from datetime import datetime as dt
from json import dumps
from os import environ
from time import time

from aiohttp import web
from aiohttp_jinja2 import get_env as jinja2_env
from aiohttp_jinja2 import setup as jinja2_setup
from aiohttp_jinja2 import template
from dotenv import load_dotenv
from emoji import demojize, emojize
from jinja2 import FileSystemLoader

from admin import AdminApp
from assets import CustomApp, Database
from files import FileRoutes
from middlewares import Middlewares

# Create app
app = CustomApp(middlewares=Middlewares)
routes = web.RouteTableDef()
app.router.add_static("/static", "./static")
jinja2_setup(app, loader=FileSystemLoader("./templates"))
load_dotenv()

# Parse .env config
app.args = dict(
    host=environ.get("HOST", None),
    port=int(environ.get("PORT", 80)),
    noadmin=False if environ.get("NO_ADMIN", "False").upper() == "FALSE" else True,
    printmessages=True
    if environ.get("PRINT_MESSAGES", "True").upper() == "TRUE"
    else False,
    databaseurl=environ.get("DATABASE_URL"),
    maxcachemessagelegth=int(environ.get("MAX_CACHE_MESSAGE_LENGTH", 0)),
    logmode=environ.get("LOG_MODE", "a"),
    logpings=True if environ.get("LOG_PINGS", "False").upper() == "TRUE" else False,
)

# Frontend Routes
@routes.get("/", name="index")
@template("index.jinja")
async def index(request: web.Request):
    return dict(request=request)


@routes.get("/offline")
@template("offline.jinja")
async def offline(request: web.Request):
    return dict(request=request)


@routes.get("/login", name="login")
@template("login.jinja")
async def login(request):
    token = request.cookies.get("sleuth_token")
    tokens = app.tokens
    rtokens = {v: k for k, v in tokens.items()}

    # Check if user has already authenticated but was not logged in
    if token in rtokens:
        return web.HTTPFound(request.app.router["index"].url_for())

    # User has not yet authenticated
    return dict(request=request)


@routes.get("/chat/", name="chat")
@template("chat.jinja")
async def chat(request):
    token = request.cookies.get("sleuth_token")
    name = app.rtokens.get(token)
    cauth = app.tokens.get(name)

    # Auth checks
    if any((not cauth, cauth != token)):
        return web.HTTPFound("/login")

    # Passed auth checks
    return dict(name=name, request=request)


# Backend Routes
@routes.post("/login")
async def login_backend(request):
    data = await request.post()

    # Grab the required stuff
    name = data.get("user")
    _pass = data.get("pass")
    success = web.HTTPFound(request.app.router["index"].url_for())
    fail = web.HTTPFound(request.app.router["login"].url_for())

    # Check the creds with the database
    print(f"Attempted login with creds: {data}", end=" - ")
    with Database() as db:
        if not db.is_valid_login(name, _pass):
            print("Login failed")
            return fail
        print("Login succeeded")

    # If a cookie/token does not exist, it creates one
    user_token = app.tokens.get(name)
    if not user_token:
        with Database() as db:
            db.set_user_token(name, app.gen_token())
    success.set_cookie("sleuth_token", app.tokens.get(name))

    return success


@routes.get("/logout")
async def logout_backend(request: web.Request):
    resp = web.HTTPFound("/")
    resp.del_cookie("sleuth_token")

    return resp


@routes.get("/redirect")
async def redirect_backend(request: web.Request):
    if request.query.get("r"):
        return web.HTTPFound(request.query.get("r"))
    return web.HTTPFound("/")


# Websocket stuff
@routes.get("/websockets/{token}/")
async def chat_backend(request):
    token = request.match_info["token"]
    ws = web.WebSocketResponse()
    name = app.rtokens.get(token)

    await ws.prepare(request)
    await send("system", f"{name} joined the chat", "user_join")

    for text in list(app.history):
        await ws.send_str(dumps(text))
    app.websockets.add(ws)

    try:
        async for msg in ws:
            if msg.type == 1:
                if msg.data == "":
                    if app.args["logpings"]:
                        print(f"Pinged by {name} at {time()}!")
                else:
                    # Max 200 characters
                    await send(name, msg.data[:200])
            elif msg.type == 258:
                print("WebSocket connection closed with exception %s" % ws.exception())
    finally:
        app.websockets.remove(ws)
        await send("system", f"{name} left the chat", "user_leave")
    return ws


# Send function
async def send(name, content, _type="message"):
    """Send a message to all websockets"""
    text = emojize(content, use_aliases=True)
    data = dict(
        type=_type,
        content=text,
        timestamp=round(time(), 2),
        author=name,
        id=app.create_message_id(),
    )
    fmt = f"{dt.fromtimestamp(data['timestamp']):%H:%M:%S} - {data['author']}: {data['content']}"

    tasks = set()
    app.history.append(data)
    if app.args["printmessages"]:
        print(demojize(fmt))
    if app.args["maxcachemessagelegth"] != 0:
        if len(app.history) > app.args["maxcachemessagelegth"]:
            del app.history[:10]

    for ws in app.websockets:
        tasks.add(create_task(ws.send_str(dumps(data))))
    while tasks:
        done, tasks = await wait(tasks)


# Finally run the damn thing
if __name__ == "__main__":
    # Add routes
    if not app.args["noadmin"]:
        app.add_subapp("/a", AdminApp)
    app.add_routes(routes)
    app.add_routes(FileRoutes)

    # Add globals
    env = jinja2_env(app)
    env.globals.update(app=app)

    # Run the app
    app.run()
