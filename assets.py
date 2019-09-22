from asyncio import create_task
from asyncio import run as run_coro
from datetime import datetime as dt
from os import getenv
from secrets import token_urlsafe as gen_token
from time import time

from aiohttp import web
from dotenv import load_dotenv
from psycopg2 import connect, ProgrammingError
from sqlparse import parse as sqlparse


# CustomApp
class CustomApp(web.Application):
    """A custom class for the app coz I'm obsessed with classes"""

    def __init__(self, *args, **kwargs):
        self.config = dict(user_tokens=dict(), master_token=gen_token(43))
        self.master_token = gen_token(43)
        self._tokens = dict()
        self.database = Database()
        self.gen_token = gen_token
        self.args: dict

        with self.database as db:
            d = db.get_all_user_creds()
            self.user_conversion = {
                i:(d[i]["realname"], d[i]["nickname"])
                for i in sorted(d) if not d[i]["suspended"]}

        self._current_message_id = 1
        self.history = list()
        self.websockets = set()
        return super().__init__(*args, **kwargs)

    # Core functions
    def run(self, *args, **kwargs):
        """Run the app using the ``args`` and ``kwargs``
        provided into the default ``web.run_app`` function.\n
        If ``host`` and ``port`` are provided in the kwargs,
        they will be overwritten by ``self.args``"""
        kwargs["host"] = self.args["host"]
        kwargs["port"] = self.args["port"]

        web.run_app(self, *args, **kwargs)

    # Decorators
    def admin_required(self, f):
        """A decorator that requires the user be
        logged in as an admin to access the page"""

        def predicate(request: web.Request):
            token = request.cookies.get("sleuth_token")
            tokens = self.config["user_tokens"]
            rtokens = {v: k for k, v in tokens.items()}
            user = rtokens.get(token)

            # Actually check the auth
            if user is None:
                return web.json_response(
                    dict(
                        status=401,
                        message="You need to be logged in to access this resource",
                    )
                )
            with self.database as db:
                if not any((db.is_admin(user), token == self.config["master_token"])):
                    return web.json_response(
                        dict(
                            status=403,
                            message="You do not have sufficient permissions to access this resource",
                        )
                    )

            # It seems we passed ¯\_(ツ)_/¯
            return f(request)

        return predicate

    def login_required(self, f):
        """A decorator that requires the user be 
        logged in (as anyone) to access the page"""

        def predicate(request: web.Request):
            token = request.cookies.get("sleuth_token")
            tokens = self.tokens
            rtokens = {v: k for k, v in tokens.items()}
            user = rtokens.get(token)

            # Actually check the auth
            if user is None:
                return web.json_response(
                    dict(
                        status=401,
                        message="You need to be logged in to access this resource",
                    )
                )

            # It seems we passed ¯\_(ツ)_/¯
            return f(request)

        return predicate

    # Properties
    @property
    def tokens(self) -> dict:
        with self.database as db:
            return db.get_all_tokens()

    @property
    def usercreds(self) -> dict:
        with self.database as db:
            return db.get_all_user_creds()

    @property
    def rtokens(self) -> dict:
        return {v: k for k, v in self.tokens.items()}

    @property
    def nicknamenonolist(self) -> list:
        with self.database as db:
            b = set()
            for i in db("SELECT username, nickname FROM users"):
                b.add(i[0])
                b.add(i[1])
            b.discard("")
            return list(b)

    def create_message_id(self) -> int:
        """Creates a unique message ID"""
        self._current_message_id += 1
        return self._current_message_id - 1

    def is_admin(self, user):
        with self.database as db:
            return db.is_admin(user)


# Database
class Database(object):
    """I made my own database wrapper lol I'm so special.\n
    TODO: Add ratelimiting to querying the actual database
    to decrease page load time."""

    # Inbuilt methods
    def __init__(self, *, load_env=True):
        """Init the class"""
        if load_env:
            load_dotenv()
        self.last_query_time = dt.now()
        self.cache = dict()

        return super().__init__()

    def __enter__(self):
        """Initialise the connection"""
        self.conn = connect(getenv("DATABASE_URL"))
        self.cursor = self.conn.cursor()
        # self.update_cache()
        # TODO: actually pull from cache and not just ignore it
        return self

    def __exit__(self, *args):
        """Close the connection"""
        self.conn.close()

    def __call__(self, query):
        """Execute raw SQL"""
        b = sqlparse(query)[0].tokens
        if b[0].value == "select":
            print("this was a select statement!")

        try:
            self.cursor.execute(query)
            result = self.cursor.fetchall()
        except ProgrammingError as e:
            result = e
        
        self.conn.commit()
        return result

    # Helper functions
    async def _update_cache(self, *, force=False):
        """Updates the internal cache list from the database.\n
        ``force`` specefies whether to bypass the ratelimit and
        just update the database (screw the consequenses).\n
        This is an asyncronous function, it is recommended to call
        the normal version, ``update_cache``"""
        # TODO: This looks like shit and makes me want to puke. FIX IT REEE
        # Chooses if either 15 mins have passed or `force` param was passed
        print("15 seconds passed", (dt.now() - self.last_query_time).seconds >= 15 * 60)
        print("force", force)
        print("empty cache", getattr(self, "cache", dict()) == dict())
        p = any(
            (
                (dt.now() - self.last_query_time).seconds >= 15 * 60,
                bool(force),
                getattr(self, "cache", dict()) == dict(),
            )
        )
        if p != True:
            return print('"p" is not true! Aborting!')
        print('"p" is true! Continuing!')

        cache = dict()
        print(time(), "Cache updating...")
        cache["usercreds"] = {
            u[0]: {"pass": u[1], "suspended": u[2], "admin": u[3]}
            for u in self("SELECT * FROM usercreds")
        }
        cache["usertokens"] = {u[0]: u[1] for u in self("SELECT * FROM usertokens")}
        self.cache = cache  # Overwrites the old cache

    def update_cache(self, *, force=False):
        """Update the cache.\n
        This is a helper function to ``await`` the
        above ``_update_cache`` function"""
        return run_coro(self._update_cache(force=force))

    # Initialize the database in case it was reset
    def init_db(self):
        """Initialise the database from a fresh start
        with all the setup required for the app."""
        self(f"""
            CREATE TABLE users (
                username VARCHAR(30) NOT NULL,
                password VARCHAR(30) NOT NULL,
                realname VARCHAR(30) NOT NULL,
                nickname VARCHAR(30) NOT NULL DEFAULT '',
                token VARCHAR(43) NOT NULL DEFAULT '',
                suspended INTEGER NOT NULL DEFAULT 0,
                admin INTEGER NOT NULL DEFAULT 0
            );
        """)

    # User creation/deletion
    def create_user(self, username, password, realname, *, nickname='', token=gen_token(), suspended=0, admin=0):
        """Registers a user into the database and returns said user.
        If the username already exists, a user will not be created"""
        return self(f"INSERT INTO users VALUES ('{username}', '{password}', '{realname}', '{nickname}', '{token}', {suspended}, {admin});")

    def delete_user(self, username):
        """Deletes a user from the database.
        **This is different from ``suspend_user``**"""
        return self(f"DELETE FROM users WHERE username='{username}'")

    def is_valid_login(self, username, password):
        """Attempts to 'login' to the database using the provided credentials
        If login succeeded, this will return `True`, else: `False`"""
        return bool(
            self(
                f"SELECT * FROM users WHERE username='{username}' AND password='{password}' AND suspended=0"
            )
        )

    # Commands regarding user suspension
    def suspend_user(self, username):
        """Suspends a user from logging in, essentially locking them from the chat"""
        return self(f"UPDATE users SET suspended=1 WHERE username='{username}'")

    def unsuspend_user(self, username):
        """Unsuspends a user from logging in, allowing them to log in again"""
        return self(f"UPDATE users SET suspended=0 WHERE username='{username}'")

    def is_suspended(self, username):
        """Will return `True` if a user is suspended, otherwise `False`.\n
        If a user is suspended but also an admin, suspended will overrule
        and this will return `True`"""
        return bool(
            self(f"SELECT * FROM users WHERE username='{username}' AND suspended=1")
        )

    # Commands regarding user admin status
    def give_user_admin(self, username, level=1):
        """Gives a user admin permissions. The level can be
        determined via the `level` paramater"""
        return self(f"UPDATE users SET admin={level} WHERE username='{username}'")

    def remove_user_admin(self, username):
        """Removes admin access from a user"""
        return self(f"UPDATE users SET admin=0 WHERE username='{username}'")

    def is_admin(self, username):
        """Will return `True` if a user is an admin, otherwise `False`.\n
        If a user is admin but also suspended, suspended will overrule
        and this will return `False`"""
        return bool(self(f"SELECT * FROM users WHERE username='{username}' AND ADMIN>0 AND suspended=0"))
    
    def get_admin_level(self, username):
        """Returns the admin level of a user, if a user has an admin level
        of `0`, they are not actually an admin. The current levels supported
        are `0`, `1` and `2`."""
        return int(self(f"SELECT admin FROM users WHERE username='{username}'")[0][0])

    # Nicknames
    def get_user_nickname(self, username):
        return self(f"SELECT nickname FROM users WHERE username='{username}'")[0][0]
    
    def set_user_nickname(self, username, nickname):
        return self(f"UPDATE users SET nickname='{nickname}' WHERE username='{username}'")

    # Tokens
    def get_user_token(self, username):
        """Get the users token from the database"""
        p = self(f"SELECT token FROM users WHERE username='{username}'")[0][0]
        if bool(p): return p
        return self.set_user_token(username)

    def set_user_token(self, username, token=gen_token()):
        """Set the users token into the database
        Returns the token match that was created"""
        self(f"UPDATE users SET token='{token}' WHERE username='{username}'")
        return token

    # A bunch more functions
    def get_all_tokens(self):
        """Get all the tokens stored in the database"""
        return dict(self("SELECT username, token FROM users"))

    def get_all_user_creds(self):
        """Returns all the user creds stored in teh database"""
        creds = {}
        for cred in self("SELECT * FROM users"):
            creds[cred[0]] = dict(password=cred[1], realname=cred[2], nickname=cred[3], token=cred[4], suspended=cred[5], admin=cred[6])
        return creds


# Experimental tests
if __name__ == "__main__":
    load_dotenv()
    with Database() as db:
        """Execute some SQL for server testing"""

        d = db("SELECT username, nickname FROM users")
        b = set()
        for i in d:
            b.add(i[0])
            b.add(i[1])
        b.discard("")
        print(f"{d}\n\n\n{b}\n\n\n{list(b)}")
