from json import dumps
from logging import Formatter, getLogger
from os import environ
from time import time

from aiohttp import web
from aiohttp_jinja2 import get_env as jinja2_env
from aiohttp_jinja2 import setup as jinja2_setup
from aiohttp_jinja2 import template
from dotenv import load_dotenv
from humanize import naturaltime
from jinja2 import FileSystemLoader

import chat
from admin import AdminApp, AdminRoutes, APIRoutes
from assets import CustomApp, Database, ThreadedHTTPHandler
from files import FileRoutes
from middlewares import Middlewares

# Create app
app = CustomApp(middlewares=Middlewares)
routes = web.RouteTableDef()
chat.app = app
app.router.add_static("/static", "./static")
jinja2_setup(app, loader=FileSystemLoader("./templates"))
load_dotenv()

# Parse .env config
app.args = dict(
    host=environ.get("HOST", None),
    port=int(environ.get("PORT", 80)),
    printmessages=True
    if environ.get("PRINT_MESSAGES", "True").upper() == "TRUE"
    else False,
    databaseurl=environ["DATABASE_URL"],
    maxcachemessagelegth=int(environ.get("MAX_CACHE_MESSAGE_LENGTH", 0)),
    logpings=True if environ.get("LOG_PINGS", "False").upper() == "TRUE" else False,
    development=True
    if environ.get("DEVELOPMENT", "False").upper() == "TRUE"
    else False,
    commandprefix=environ.get("COMMAND_PREFIX", "!"),
    nicknamecooldown=int(environ.get("NICKNAME_COOLDOWN", 0)),
)

# Frontend Routes
@routes.get("/", name="index")
@template("index.jinja")
async def index(request: web.Request):
    return dict(request=request)

@routes.get("/device")
async def device(request: web.Request):
    ua = request.headers["User-Agent"]
    m = await app.is_mobile(request)
    return web.Response(body=f"{ua}\n\n{m}")


@routes.get("/offline", name="offline")
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


@routes.get("/settings", name="settings")
@template("settings.jinja")
@app.login_required
async def settings(request: web.Request):
    name = app.rtokens[request.cookies["sleuth_token"]]
    return dict(request=request, name=name)


@routes.get("/chat/", name="chat")
@template("chat.jinja")
async def chat_route(request: web.Request):
    token = request.cookies.get("sleuth_token")
    name = app.rtokens.get(token)
    cauth = app.tokens.get(name)

    # Auth checks
    if any((not cauth, cauth != token)):
        return web.HTTPFound(f"/login?next={request.rel_url}")

    # Passed auth checks
    return dict(name=name, request=request)


# Backend Routes
@routes.post("/login")
async def login_backend(request: web.Request):
    data = await request.post()

    # Grab the required stuff
    name = data.get("user")
    _pass = data.get("pass")
    nxt = request.url.query.get("next")
    success = web.HTTPFound(nxt or request.app.router["index"].url_for())
    fail = web.HTTPFound(
        str(request.app.router["login"].url_for())
        + (f"?incorrect&next={nxt}" if nxt else "?incorrect")
    )

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


@routes.get("/menu")
@template("menu.jinja")
async def menu():
    return dict()


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
    ws.name, ws.token = name, token
    ws.admin = app.is_admin(name)
    await ws.prepare(request)

    if token not in app.rtokens.keys():
        await chat.send_to_ws(
            ws,
            content="Your authentication token is invalid. "
            "Please re-login to join the chat",
        )
        await ws.close(message=b"Invalid login token")
        return ws

    # Store the user's settings on the websocket
    with app.database as db:
        ws.nickname = db.get_user_nickname(ws.name)
        if db.is_suspended(name):
            # Disallow suspended users to join chat
            await chat.send_to_ws(
                ws,
                content="Your account has been suspended from joining the chat, "
                "please try to rejoin again later",
            )
            await ws.close(message=b"Your account is suspended")
            return ws
    # TODO: WebSocket only "opens" when all the messages from history have been loaded in
    # could just make a server message with a type of "messages_loaded" or smtn

    if app.websockets == set():
        app.log.info("SERVER_RESTART", dict(type="server_restart"))

    await chat.send("system", f"{name} joined the chat", type="user_join")

    for msg in app.history:
        await ws.send_json(msg)
    app.websockets.add(ws)
    await chat.process_commands(ws, f"{app.args['commandprefix']}active")

    try:
        async for msg in ws:
            if msg.type == 1:
                if msg.data == "":
                    if app.args["logpings"]:
                        print(f"Pinged by {name} at {time()}!")
                else:
                    a = await chat.process_commands(ws, msg.data[:200])
                    b = await chat.process_admin_commands(ws, msg.data[:200])
                    if bool(a) and bool(b):
                        await chat.send(ws, msg.data[:200])
            elif msg.type == 258:
                print(
                    f'WebSocket for "{ws.name}" connection closed with exception %s'
                    % ws.exception()
                )
    finally:
        app.websockets.discard(ws)
        await chat.send("system", f"{name} left the chat", type="user_leave")
    return ws


# App helper functions
async def on_shutdown(app: CustomApp):
    for ws in app.websockets.copy():
        await ws.close(message=b"The server is shutting down")
        import device_detector


# Finally run the chat
if __name__ == "__main__":
    # Set up logging
    app.log = getLogger("msglog")
    if app.args["development"]:
        app.log.addHandler(
            ThreadedHTTPHandler(
                host="sleuth-logs.chocolatejade42.repl.co",
                url=f"/new?token={environ.get('LOGS_AUTH_TOKEN')}",
                method="POST",
            )
        )
    # msglog.addHandler()
    app.log.setLevel(20)

    # Add routes
    app.add_subapp("/a", AdminApp)
    app.add_routes(routes)
    app.add_routes(FileRoutes)

    # Add app config functions
    app.on_shutdown.append(on_shutdown)
    #app.on_startup.append(on_startup)

    # Add globals
    env = jinja2_env(app)
    env.globals.update(app=app, adminroutes=AdminRoutes, apiroutes=APIRoutes)
    env.globals.update(development=app.args["development"], len=len, all=all)

    # Run the app
    app.run()
