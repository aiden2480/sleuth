from aiohttp import web
from aiohttp_jinja2 import template, setup as jinja2_setup, get_env as jinja2_env
from argparse import ArgumentParser
from asyncio import create_task, wait
from datetime import datetime as dt
from dotenv import load_dotenv
from emoji import emojize, demojize
from jinja2 import FileSystemLoader
from logging import Formatter, FileHandler, getLogger
from os import environ
from secrets import token_urlsafe as gen_token

from admin import routes as AdminRoutes, AdminApp
from assets import Database, CustomApp
from middlewares import Middlewares

# Create app
app = CustomApp(middlewares= Middlewares)
app.router.add_static("/assets", "./static")
jinja2_setup(app, loader=FileSystemLoader("./templates"))

# Setup config
history = list()
websockets = set()
routes = web.RouteTableDef()
load_dotenv()

# Parse args
parser = ArgumentParser(description="Startup options for the chat app")
parser.add_argument("-host", type=str, default=None, help="Override the default host")
parser.add_argument("-port", type=int, default=80, help="Override the default port provided in the env")
parser.add_argument("--noadmin", default= False, action="store_true", help= "Specefies whether to add the admin routes or not")
parser.add_argument("--print-messages", default=True, action="store_true", help="Specefies whether to print user messages or not")
parser.add_argument("--database", type=str, default=environ.get("DATABASE_URL"), help="Specefies the postgres URL of the databasse")
parser.add_argument("--delete-cache-messages", type=int, default=0, metavar="NUM_OF_MESSAGES", help="The length of which the server-cached messages must be before they are deleted. 0 for don't delete")
parser.add_argument("--log-mode", type=str, default= "a", metavar="MODE", help= "The filemode in which to open the log file")
app.args = args = parser.parse_args()

# Setup logging
logger = getLogger("aiohttp.access")
logger.setLevel(10)
handler = FileHandler("temp/website.log", encoding="utf-8", mode= args.log_mode)
handler.setFormatter(Formatter("[%(asctime)s] [%(levelname)s]: %(message)s"))
logger.addHandler(handler)
logger.debug((
    "=   SERVER STARTED   ="
    f"\n\tMaster access token: {app.master_token!r}\n"
))
app.logger = logger

# Frontend Routes
@routes.get("/", name="index")
@template("index.jinja")
async def index(request):
    return dict(request= request)


@routes.get("/login", name= "login")
@template("login.jinja")
async def login(request):
    token = request.cookies.get("token")
    tokens = app.tokens
    rtokens = {v:k for k,v in tokens.items()}
    
    # Check if user has already authenticated but was not logged in
    if token in rtokens:
        return web.HTTPFound(request.app.router["chat"].url_for())

    # User has not yet authenticated
    return dict(request= request)


@routes.get("/chat/", name="chat")
@template("chat.jinja")
async def chat(request):
    token = request.cookies.get("token")
    name = app.rtokens.get(token)
    cauth = app.tokens.get(name)

    # Auth checks
    if any((not cauth, cauth != token)):
        return web.HTTPFound("/")

    # Passed auth checks
    return dict(name= name, request= request)


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
            db.set_user_token(name, gen_token())
    success.set_cookie("token", app.tokens.get(name))

    return success


@routes.get("/logout")
async def logout_backend(request: web.Request):
    resp = web.HTTPFound("/")
    resp.del_cookie("token")

    return resp


@routes.get("/websockets/{token}/")
async def chat_backend(request):
    token = request.match_info["token"]
    ws = web.WebSocketResponse()
    name = app.rtokens.get(token)

    await ws.prepare(request)
    await send_fn("system", f"{name} joined the chat")

    for text in list(history):
        await ws.send_str(text)
    websockets.add(ws)

    try:
        async for msg in ws:
            if msg.type == 1:
                await send_fn(name, msg.data)
            elif msg.type == 258:
                print("ws connection closed with exception %s" % ws.exception())
    finally:
        websockets.remove(ws)

    await send_fn("system", f"{name} left the chat")
    return ws

# Send function
async def send_fn(name, message):
    text = emojize(f"{dt.now():%H:%M:%S} - {name}: {message}", use_aliases=True)
    history.append(text)

    if args.print_messages:
        print(demojize(text))
    if args.delete_cache_messages != 0:
        if len(history) > args.delete_cache_messages:
            del history[:10]

    tasks = set()
    for ws in websockets:
        tasks.add(create_task(ws.send_str(text)))
    while tasks:
        done, tasks = await wait(tasks)


# Finally run the damn thing
if __name__ == "__main__":
    try:
        # Add routes
        if not args.noadmin:
            app.add_subapp("/a", AdminApp)
        app.add_routes(routes)
        
        # Add globals
        env = jinja2_env(app)
        env.globals.update(app= app)

        # Run the app
        app.run(host= args.host, port= environ.get("PORT", args.port))
    finally:
        logger.debug("=  SERVER SHUT DOWN  =")
