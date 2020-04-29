from asyncio import create_task, wait
from datetime import datetime as dt
from datetime import timedelta as td
from json import dumps
from os import environ
from time import time

from aiohttp import web
from aiohttp_jinja2 import get_env as jinja2_env
from aiohttp_jinja2 import setup as jinja2_setup
from aiohttp_jinja2 import template
from dotenv import load_dotenv
from emoji import demojize, emojize
from humanize import naturaltime
from jinja2 import FileSystemLoader

from admin import AdminApp, AdminRoutes
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
async def chat(request: web.Request):
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
    fail = web.HTTPFound(str(request.app.router["login"].url_for()) + "?incorrect")

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
        await ws.prepare(request)
        await send_to_ws(ws, content="Your authentication token is invalid. " \
            "Please re-login to join the chat")
        await ws.close(message=b"Invalid login token")
        return ws

    # Store the user's settings on the websocket
    with app.database as db:
        ws.nickname = db.get_user_nickname(ws.name)
        if db.is_suspended(name):
            # Disallow suspended users to join chat
            await ws.prepare(request)
            await send_to_ws(ws, content="Your account has been suspended from joining the chat, " \
                "please try to rejoin again later")
            await ws.close(message=b"Your account is suspended")
            return ws
    # TODO: WebSocket only "opens" when all the messages from history have been loaded in

    await ws.prepare(request)
    await send("system", f"{name} joined the chat", type="user_join")

    for msg in list(app.history):
        await ws.send_json(msg)
    app.websockets.add(ws)
    await process_commands(ws, f"{app.args['commandprefix']}active")

    try:
        async for msg in ws:
            if msg.type == 1:
                if msg.data == "":
                    if app.args["logpings"]:
                        print(f"Pinged by {name} at {time()}!")
                else:
                    a = await process_commands(ws, msg.data[:200])
                    b = await process_admin_commands(ws, msg.data[:200])
                    if bool(a) and bool(b):
                        await send(ws, msg.data[:200])
            elif msg.type == 258:
                print(
                    f'WebSocket for "{ws.name}" connection closed with exception %s'
                    % ws.exception()
                )
    finally:
        app.websockets.discard(ws)
        await send("system", f"{name} left the chat", type="user_leave")
    return ws


# Cleanup function
async def on_shutdown(app: CustomApp):
    for ws in app.websockets.copy():
        await ws.close(message=b"The server is shutting down")


# Exclusively chat functions
# Does this need to be moved to a seperate file?
async def process_commands(ws: web.WebSocketResponse, content: str) -> bool:
    """Returns if the process should carry on and send the message.
    If this returns `True`, the message was not a command and should
    be sent. If this returns `None` or `False`, the message should
    not be sent"""
    # FIXME: This needs to be re-styled because it currently looks like shit
    if not content.startswith(app.args["commandprefix"]):
        return True
    cmd = content.split()[0][1:].lower()
    args = content.split()[1:]

    if cmd in ["active", "online"]:
        # p = ("Other users in chat: "+ ", ".join([w.name for w in app.websockets if w != ws])) if len(app.websockets) > 1 else "No one else is currently in chat"
        p = ((
                "Other users in chat: "
                + ", ".join([
                    (f'{w.name} as "{w.nickname}"' if w.nickname else w.name)
                    for w in app.websockets
                    if w != ws
                ])
            )
            if len(app.websockets) > 1
            else "No one else is currently in chat"
        )
        await send_to_ws(ws, type="active_users", content=p)
    elif cmd in ["nick", "nickname"]:
        # TODO: do `clearall` before time check so you can always clear usernames if you are admin
        d = app.last_nick_change[ws.name] + td(seconds=app.args["nicknamecooldown"])
        with app.database as db:
            if not d < dt.now():
                if not db.is_admin(ws.name):
                    return await send_to_ws(ws, content=f"Please wait before changing your nickname again. " \
                        f"You can next change your nickname {naturaltime(d)}")
        if args == []:
            return await send_to_ws(ws, content=f"You need to specify a nickname to set. " \
                "If you want to clear your nickname, use the command \"{app.args['commandprefix']}{cmd} clear\"")
        nick = " ".join(args)[:15]
        if nick.lower() in [i.lower() for i in app.nicknamenonolist]:
            return await send_to_ws(ws, content=f"This nickname is either already taken " \
                "or is someone else's username")

        # Change the nickname
        with app.database as db:
            if nick.lower() == "clear":
                db.set_user_nickname(ws.name, "")
                ws.nickname = ""
                return await send("system", f"{ws.name} has cleared their nickname")
            if nick.lower() == "clearall":
                if not db.is_admin(ws.name):
                    return await send_to_ws(ws, content="You don't have enough permissions to use this command")
                for u in db("SELECT username FROM users"):
                    usr = u[0]
                    db.set_user_nickname(usr, "")

                b = f"{ws.name} has cleared all user nicknames. "
                b += (", ".join([
                        f"{w.nickname} is now {w.name}"
                        for w in app.websockets
                        if w.nickname != ""
                    ])
                    or "No nicknames to clear"
                )

                for w in app.websockets:
                    w.nickname = ""
                return await send("system", b)

            app.last_nick_change[ws.name] = dt.now()
            db.set_user_nickname(ws.name, nick)
            ws.nickname = nick
            await send("system", f"{ws.name} has changed their nickname to {nick}")
    elif cmd in ["del", "delete"]:
        pass # Don't show a message
        # TODO: Make it so a user can delete their own messages even if they don't have admin
    else:
        return True


async def process_admin_commands(ws: web.WebSocketResponse, content: str) -> bool:
    """Returns if the process should carry on and send the message.
    If this returns `True`, the message was not a command and should
    be sent. If this returns `None` or `False`, the message should
    not be sent"""
    if not all((content.startswith(app.args["commandprefix"]), ws.admin)):
        return True
    cmd = content.split()[0][1:].lower()
    args = content.split()[1:]

    # FIXME: If a user tries to kick/suspend a user that doesn't exist, they get disconnected
    if cmd in ["kick"]:
        if args == []:
            return
        # `usr` is the user we are trying to kick
        args = [i for i in args if i.lower() != ws.name.lower()]  # Can't kick yourself
        usr = args[0].lower()
        reason = " ".join(args[1:]) if len(args) > 1 else "No reason provided"
        k = ""

        if args == []:
            return

        with app.database as db:
            if usr not in db.get_all_usernames():
                return await send_to_ws(ws, content=f"The user {usr} is not registered in the system")
            if db.get_admin_level(usr) > db.get_admin_level(ws.name):
                return await send_to_ws(ws, content=f"You can't kick {usr} because they " \
                    "have a higher admin level than you")
            for w in app.websockets.copy():
                if w.name.lower() == usr:
                    await w.close(message=f'Kicked by {ws.name} for "{reason}"')
                    app.websockets.discard(w)
                    k = usr
        if not k:
            return
        await send("system", f"{ws.name} has kicked user {k}", type="user_kick")
    elif cmd in ["suspend"]:
        with app.database as db:
            if usr not in db.get_all_usernames():
                return await send_to_ws(ws, content=f"The user {usr} is not registered in the system")
            if db.get_admin_level(args[0]) > db.get_admin_level(ws.name):
                return await send_to_ws(ws, content=f"You can't suspend {args[0]} because " \
                    "they have a higher admin level than you")
        if args == []:
            return
        await process_admin_commands(ws, f"!kick {args[0]}")
        with app.database as db:
            db.suspend_user(args[0])
    elif cmd in ["unsuspend"]:
        if args == []:
            return
        with app.database as db:
            db.unsuspend_user(args[0])
    elif cmd in ["delete", "del"]:
        # Admins can remove any message not sent by system
        if not args[0].isdigit():
            return await send_to_ws(ws, content="The message ID must be a number")
        m = int(args[0])
        for msg in app.history.copy():
            if msg["id"] == m:
                if msg["author"] == "system":
                    return await send_to_ws(ws, content="You can't delete this message as it is a system message 😟")

        # Remove message from history
        for msg in app.history.copy():
            if msg["id"] == m:
                app.history.remove(msg)

        # Broadcast that a message was deleted
        tasks = set()
        for w in app.websockets:
            tasks.add(create_task(w.send_json(dict(type="message_delete", content=str(m)))))
        while tasks:
            done, tasks = await wait(tasks)
        # TODO: Make a non-admin version of this where any user can delete their own message
    else:
        return True


async def send(*args, **kwargs):
    """Send a message to all websockets.
    If the first argument in `args` is a websocket, name and nickname will be pulled from that. """
    # Decode the args
    if isinstance(args[0], web.WebSocketResponse):
        name = args[0].name
        nickname = args[0].nickname
        content = args[1]
    else:
        name = args[0]
        nickname = ""
        content = args[1]
    typ = kwargs.pop("type", "message")  # "message" is default

    text = emojize(content, use_aliases=True)
    data = dict(
        type=typ,
        content=text,
        timestamp=round(time(), 2),
        author=name,
        id=app.create_message_id(),
    )
    if nickname:
        data["nickname"] = nickname
    fmt = f"{dt.fromtimestamp(data['timestamp']):%H:%M:%S} - {data['author']}: {data['content']}"

    # Config
    tasks = set()
    app.history.append(data)
    if app.args["printmessages"]:
        print(demojize(fmt))
    if app.args["maxcachemessagelegth"] != 0:
        if len(app.history) > app.args["maxcachemessagelegth"]:
            del app.history[:10]

    # Send the message to all websockets
    for ws in app.websockets:
        tasks.add(create_task(ws.send_json(data)))
    while tasks:
        done, tasks = await wait(tasks)


async def send_to_ws(ws: web.WebSocketResponse, **kwargs):
    """Sends a message to a single websocket, rather than
    all of them\n
    `kwargs` is dumped via `json.dumps` and then sent to the websocket.
    If `author` is not supplied, a default of `system` is used.
    Likewise with `type`, default is `message`"""
    if not kwargs.get("author"):
        kwargs["author"] = "system"
    if not kwargs.get("type"):
        kwargs["type"] = "message"
    await ws.send_json(kwargs)


# Finally run the chat
if __name__ == "__main__":
    # Add routes
    app.add_subapp("/a", AdminApp)
    app.add_routes(routes)
    app.add_routes(FileRoutes)

    # Add shutdown function
    app.on_shutdown.append(on_shutdown)

    # Add globals
    env = jinja2_env(app)
    env.globals.update(app=app, adminroutes=AdminRoutes)
    env.globals.update(development=app.args["development"], len=len)

    # Run the app
    app.run()
