from aiohttp import WSMsgType, ClientSession, ClientConnectionError, web
from asyncio import create_task, wait, get_event_loop, run
from datetime import datetime as dt
from helpers import Database
from logging import getLogger, FileHandler, Formatter
from multiprocessing import Process

# Setup
routes = web.RouteTableDef()
websockets = set()
history = []

# Routes
@routes.get("/", name= "index")
async def hello(request):
    with open("assets/templates/index.html", "rb") as f:
        return web.Response(body= f.read().decode("utf8"), content_type= "text/html")

@routes.post("/")
async def login(request):
    form_data = await request.post()
    success = lambda name: web.HTTPFound(request.app.router["chat"].url_for(name= name))
    fail = lambda: web.HTTPFound(request.app.router["index"].url_for())

    name = form_data.get("user")
    _pass = form_data.get("pass")
    print(f"Attempted login with creds: {form_data}")
    
    if not all((name, _pass)):
        return fail()
    
    with Database() as db:
        unotlying = db.valid_login(name, _pass)
    
    if not unotlying:
        return fail()
    
    return web.HTTPFound(request.app.router["chat"].url_for(name= name))

@routes.get("/{name}/", name= "chat")
async def chat_page(request):
    with open("assets/templates/chat.html", "rb") as f:
        return web.Response(body= f.read().decode("utf8"), content_type= "text/html")

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

@routes.get("/assets/js/chat.js")
async def js(request):
    with open("assets/static/chat.js") as f:
        return web.Response(body= f.read(), content_type= "text/javascript")


# Send function
async def send_to_all(name, message):
    now = dt.now()
    text = f"{now:%H:%M:%S} – {name}: {message}"

    history.append(text)
    if len(history) > 20:
        del history[:10]

    tasks = set()
    for ws in websockets:
        tasks.add(create_task(ws.send_str(text)))
    while tasks:
        done, tasks = await wait(tasks)


# Updating messages in the console
async def client():
    loop = get_event_loop()
    
    while True:
        async with ClientSession(loop= loop) as sess:
            try:
                async with sess.get("http://localhost:80") as resp:
                    break
            except ClientConnectionError:
                continue

    async with ClientSession(loop= loop).ws_connect("http://localhost:80/CLI/ws/") as ws:
        async for msg in ws:
            if msg.type == WSMsgType.TEXT:
                data = msg.data.strip()
                print(data)
            elif msg.type == WSMsgType.CLOSED:
                break
            elif msg.type == WSMsgType.ERROR:
                break

def run_client():
    run(client())


# Finally run the damn thing
if __name__ == "__main__":
    logger = getLogger("aiohttp.access")
    logger.setLevel(10)
    handler = FileHandler("assets/website.log", mode= "w", encoding= "utf-8")
    handler.setFormatter(Formatter("%(asctime)s: %(levelname)s:\t%(message)s"))
    logger.addHandler(handler)

    app = web.Application(logger= logger)
    app.add_routes(routes)

    try:
        p = Process(target= run_client).start()
        web.run_app(app, port= 80)
    except KeyboardInterrupt:
        p.terminate()
