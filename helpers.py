from aiohttp import ClientSession, ClientConnectionError, WSMsgType
from asyncio import run as asyncio_run
from sqlite3 import connect as sconnect, Error as sError
from psycopg2 import connect as pconnect, Error as pError

# Message client
class MessageClient(object):
    """Create a small client in the console to recieve messages"""

    def __init__(self, args):
        self.args = args

    async def client(self):
        async with ClientSession() as sess:
            while True:
                try:
                    async with sess.get(f"http://localhost:{self.args.port}") as resp:
                        break
                except ClientConnectionError:
                    continue

        async with ClientSession().ws_connect(
            f"http://localhost:{self.args.port}/CLI/ws/"
        ) as ws:
            async for msg in ws:
                if msg.type == WSMsgType.TEXT:
                    data = msg.data.strip()
                    print(data)
                elif msg.type == WSMsgType.CLOSED:
                    break
                elif msg.type == WSMsgType.ERROR:
                    break

    def run(self):
        asyncio_run(self.client())


# Database
class Database(object):
    """I made my own database wrapper lol I'm so special"""

    # Inbuilt methods
    def __init__(self, useProductionDatabase=False, **kwargs):
        """Param ``useProductionDatabase`` specefies whether to use the production database
        hosted on ``Heroku`` or the local database in ``sqlite3`` format\n
        The only paramater processed by ``kwargs`` is ``location`` which would be a ``postgres`` URI if ``useProductionDatabase`` is True, otherwise it would be a location on the local disk"""

        if useProductionDatabase:
            self.databaseType = "postgres"
            self.create_conn = lambda: pconnect(
                kwargs.get(
                    "location",
                    "postgres://khcpmkfiloljcz:603026445663808d65cbb6f71fb1d73ae4e973ac7da9a9e2df13b82a57d70bc9@ec2-174-129-209-212.compute-1.amazonaws.com:5432/d35sf2687qovr6",
                )
            )
        else:
            self.databaseType = "sqlite3"
            self.create_conn = lambda: sconnect(
                kwargs.get("location", "assets/database.db")
            )

    def __enter__(self):
        """Initialise the connection"""
        self._conn = self.create_conn()  # self.connect(self.databaseLocation)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the connection"""
        self._conn.close()
        del self

    def __call__(self, query, **context):
        """Execute raw SQL"""
        c = self._conn.cursor()
        try:
            result = c.execute(query.format(**context))
            self._conn.commit()
        except Exception as e:
            result = e
        return result

    # Custom methods
    def init_db(self, *, overwrite=True):
        """Initialise the database from a fresh start
        with all the setup required for the app."""
        return self(
            "CREATE TABLE UserCreds (user VARCHAR(15), pass VARCHAR(15), suspended BOOL)"
        )

    def create_user(self, user, _pass):
        """Registers a user into the database and returns said user.
        If the username already exists, a user will not be created"""
        p = self(f"SELECT * FROM UserCreds WHERE user='{user}'").fetchone()
        if p:
            return 1, p

        self(f"INSERT INTO UserCreds VALUES ('{user}', '{_pass}', 0)")
        return 2, self(f"SELECT * FROM UserCreds WHERE user='{user}'").fetchone()

    def is_valid_login(self, user, _pass):
        """Attempts to 'login' to the database using the provided credentials
        If login succeeded, this will return `True`, else: `False`"""
        p = self(
            f"SELECT * FROM UserCreds WHERE user='{user}' AND pass='{_pass}' AND suspended=0"
        ).fetchone()

        return bool(p)

    def suspend_user(self, user):
        """Suspends a user from logging in, essentially locking them from the chat"""
        return self(f"UPDATE UserCreds SET suspended=1 WHERE user='{user}'")

    def unsuspend_user(self, user):
        """Unsuspends a user from logging in, allowing them to log in again"""
        return self(f"UPDATE UserCreds SET suspended=0 WHERE user='{user}'")

    def is_suspended(self, user):
        """Will return `True` if a user is suspended, otherwise `False`"""
        return bool(
            self(
                f"SELECT * FROM UserCreds WHERE user='{user}' AND suspended=1"
            ).fetchone()
        )


if __name__ == "__main__":
    with Database(True) as db:
        """Execute some SQL for server testing"""
        print(db.init_db())

        print("database open")
    print("database closed")
