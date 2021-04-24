from asyncio import create_task, wait
from datetime import datetime as dt
from datetime import timedelta as td
from time import time
from aiohttp.web import WebSocketResponse
from emoji import demojize, emojize
from assets import CustomApp
app: CustomApp

# Exclusively chat functions
# Does this need to be moved to a seperate file?
async def process_commands(ws: WebSocketResponse, content: str) -> bool:
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
        p = (("Other users in chat: "+ ", ".join([(f'{w.name} as "{w.nickname}"' if w.nickname else w.name) for w in app.websockets if w != ws])) if len(app.websockets) > 1 else "No one else is currently in chat")
        await send_to_ws(ws, type="active_users", content=p)
    elif cmd in ["nick", "nickname"]:
        # TODO: do `clearall` before time check so you can always clear usernames if you are admin
        d = app.last_nick_change[ws.name] + td(seconds=app.args["nicknamecooldown"])
        with app.database as db:
            if not d < dt.now():
                if not db.is_admin(ws.name):
                    return await send_to_ws(
                        ws,
                        content=f"Please wait before changing your nickname again. "
                        "You can next change your nickname {naturaltime(d)}",
                    )
        if args == []:
            return await send_to_ws(
                ws,
                content=f"You need to specify a nickname to set. "
                "If you want to clear your nickname, use the command \"{app.args['commandprefix']}{cmd} clear\"",
            )
        nick = " ".join(args)[:15]
        if nick.lower() in [i.lower() for i in app.nicknamenonolist]:
            return await send_to_ws(
                ws,
                content=f"This nickname is either already taken "
                "or is someone else's username",
            )

        # Change the nickname
        with app.database as db:
            if nick.lower() == "clear":
                db.set_user_nickname(ws.name, "")
                ws.nickname = ""
                return await send("system", f"{ws.name} has cleared their nickname")
            if nick.lower() == "clearall":
                if not db.is_admin(ws.name):
                    return await send_to_ws(
                        ws,
                        content="You don't have enough permissions to use this command",
                    )
                for u in db("SELECT username FROM users"):
                    usr = u[0]
                    db.set_user_nickname(usr, "")

                b = f"{ws.name} has cleared all user nicknames. "
                b += (", ".join([
                            f"{w.nickname} is now {w.name}"
                            for w in app.websockets
                            if w.nickname != ""
                        ]
                    )
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
        pass  # Don't show a message
        # TODO: Make it so a user can delete their own messages even if they don't have admin
    else:
        return True


async def process_admin_commands(ws: WebSocketResponse, content: str) -> bool:
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
                return await send_to_ws(
                    ws, content=f"The user {usr} is not registered in the system"
                )
            if db.get_admin_level(usr) > db.get_admin_level(ws.name):
                return await send_to_ws(
                    ws,
                    content=f"You can't kick {usr} because they "
                    "have a higher admin level than you",
                )
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
                return await send_to_ws(
                    ws, content=f"The user {usr} is not registered in the system"
                )
            if db.get_admin_level(args[0]) > db.get_admin_level(ws.name):
                return await send_to_ws(
                    ws,
                    content=f"You can't suspend {args[0]} because "
                    "they have a higher admin level than you",
                )
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
                    return await send_to_ws(
                        ws,
                        content="You can't delete this message as it is a system message 😟",
                    )

        # Remove message from history
        for msg in app.history.copy():
            if msg["id"] == m:
                app.history.remove(msg)

        # Broadcast that a message was deleted
        tasks = set()
        for w in app.websockets:
            tasks.add(
                create_task(w.send_json(dict(type="message_delete", content=str(m))))
            )
        while tasks:
            done, tasks = await wait(tasks)
        # TODO: Make a non-admin version of this where any user can delete their own message
    else:
        return True


async def send(*args, **kwargs):
    """Send a message to all websockets.
    If the first argument in `args` is a websocket, name and nickname will be pulled from that. """
    # Decode the args
    if isinstance(args[0], WebSocketResponse):
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
        app.log.info(demojize(fmt), data)
    if app.args["maxcachemessagelegth"] != 0:
        if len(app.history) > app.args["maxcachemessagelegth"]:
            del app.history[:10]

    # Send the message to all websockets
    for ws in app.websockets:
        tasks.add(create_task(ws.send_json(data)))
    while tasks:
        done, tasks = await wait(tasks)


async def send_to_ws(ws: WebSocketResponse, **kwargs):
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
