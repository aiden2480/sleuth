from aiohttp import web
from dotenv import load_dotenv
from os import getenv
from psycopg2 import connect
from secrets import token_urlsafe as gen_token


# CustomApp
class CustomApp(web.Application):
    """A custom class for the app"""
    def __init__(self, *args, **kwargs):
        self.config = dict(user_tokens=dict(), master_token=gen_token(43))
        self.master_token = gen_token(43)
        self._tokens= {}
        return super().__init__(*args, **kwargs)
    
    # Core functions
    def run(self, *args, **kwargs):
        """Run the app using the ``args`` and ``kwargs``
        provided into the default ``web.run_app`` function"""
        web.run_app(self, *args, **kwargs)

    # Decorators
    def admin_required(self, f):
        """A decorator that requires the user be
        logged in as an admin to access the page"""
        
        def predicate(request: web.Request):
            token = request.cookies.get("token")
            tokens = self.config["user_tokens"]
            rtokens = {v:k for k,v in tokens.items()}
            user = rtokens.get(token)

            # Actually check the auth
            if user is None:
                return web.json_response(dict(
                    status= 401,
                    message= "You need to be logged in to access this resource"
                ))
            with Database() as db:
                if not any((db.is_admin(user), token==self.config["master_token"])):
                    return web.json_response(dict(
                        status= 403,
                        message= "You do not have sufficient permissions to access this resource"
                    ))

            # It seems we passed ¯\_(ツ)_/¯
            return f(request)
        return predicate

    def login_required(self, f):
        """A decorator that requires the user be 
        logged in (as anyone) to access the page"""
        
        def predicate(request: web.Request):
            token = request.cookies.get("token")
            tokens = self.app.tokens
            rtokens = {v:k for k,v in tokens.items()}
            user = rtokens.get(token)

            # Actually check the auth
            if user is None:
                return web.json_response(dict(
                    status= 401,
                    message= "You need to be logged in to access this resource"
                ))

            # It seems we passed ¯\_(ツ)_/¯
            return f(request)
        return predicate

    # Properties
    @property
    def tokens(self) -> dict:
        with Database() as db:
            return db.get_all_tokens()
    
    @property
    def usercreds(self) -> dict:
        with Database() as db:
            return db.get_all_user_creds()
    
    @property
    def rtokens(self) -> dict:
        return {v:k for k,v in self.tokens.items()}
    
    def is_admin(self, user):
        with Database() as db:
            return db.is_admin(user)


# Database
class Database(object):
    """I made my own database wrapper lol I'm so special"""

    # Inbuilt methods
    def __init__(self):
        """Init the class"""
        pass

    def __enter__(self):
        """Initialise the connection"""
        self._conn = connect(getenv("DATABASE_URL"))
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Close the connection"""
        self._conn.close()
        del self

    def __call__(self, query):
        """Execute raw SQL"""
        cur = self._conn.cursor()
        try:
            cur.execute(query)
            result = cur.fetchall()
            self._conn.commit()
        except Exception as e:
            result = e
        return result

    # Initialize the database in case it was reset
    def init_db(self, usercredsname="usercreds", usertokensname="usertokens"):
        """Initialise the database from a fresh start
        with all the setup required for the app."""
        self(f"""
            CREATE TABLE {usercredsname}(
                "name" VARCHAR (20) NOT NULL,
                "pass" VARCHAR (30) NOT NULL,
                "suspended" BOOL NOT NULL DEFAULT FALSE,
                "admin" BOOL NOT NULL DEFAULT FALSE
            )
        """)
        self(f"""
            CREATE TABLE {usertokensname}(
                "name" VARCHAR (20) NOT NULL,
                "token" VARCHAR (43) NOT NULL
            )
        """)

    # User creation/deletion
    def create_user(self, name, _pass):
        """Registers a user into the database and returns said user.
        If the username already exists, a user will not be created"""
        p = self(f"SELECT * FROM usercreds WHERE name='{name}'")
        if p: return p[0]

        self(f"INSERT INTO usercreds VALUES ('{name}', '{_pass}')")
        return self(f"SELECT * FROM usercreds WHERE name='{name}'")[0]

    def delete_user(self, name):
        """Deletes a user from the database.
        **This is different from ``suspend_user``**"""
        return self(f"DELETE FROM usercreds WHERE name='{name}'")

    def is_valid_login(self, name, _pass):
        """Attempts to 'login' to the database using the provided credentials
        If login succeeded, this will return `True`, else: `False`"""
        return bool(
            self(
                f"SELECT * FROM usercreds WHERE name='{name}' AND pass='{_pass}' AND suspended=FALSE"
            )
        )

    # Commands regarding user suspension
    def suspend_user(self, name):
        """Suspends a user from logging in, essentially locking them from the chat"""
        return self(f"UPDATE usercreds SET suspended=TRUE WHERE name='{name}'")

    def unsuspend_user(self, name):
        """Unsuspends a user from logging in, allowing them to log in again"""
        return self(f"UPDATE usercreds SET suspended=0 WHERE name='{name}'")

    def is_suspended(self, name):
        """Will return `True` if a user is suspended, otherwise `False`.\n
        If a user is suspended but also an admin, suspended will overrule
        and this will return `True`"""
        return bool(
            self(
                f"SELECT * FROM usercreds WHERE name='{name}' AND suspended=TRUE"
            )
        )
    
    # Commands regarding user admin status
    def give_user_admin(self, name):
        """Gives a user admin permissions"""
        return self(f"UPDATE usercreds SET admin=TRUE WHERE name='{name}'")

    def remove_user_admin(self, name):
        """Removes admin access from a user"""
        return self(f"UPDATE usercreds SET admin=FALSE WHERE name='{name}'")
    
    def is_admin(self, name):
        """Will return `True` if a user is an admin, otherwise `False`.\n
        If a user is admin but also suspended, suspended will overrule
        and this will return `False`"""
        return bool(self(
            f"SELECT * FROM usercreds WHERE NAME='{name}' AND ADMIN=TRUE AND suspended=FALSE"
        ))
    
    # Tokens
    def get_user_token(self, name):
        """Get the users token from the database"""
        p = self(f"SELECT * FROM usertokens WHERE NAME='{name}'")
        if bool(p):
            return p[0][1]
        return self.set_user_token(name, gen_token())[1]

    def set_user_token(self, name, token= gen_token()):
        """Set the users token into the database
        Returns the name + token match that was created"""
        self._conn.cursor().execute(f"INSERT INTO usertokens VALUES ('{name}', '{token}')")
        self._conn.commit()
        return name, token

    # A bunch more functions
    def get_all_tokens(self):
        """Get all the tokens stored in the database"""
        return dict(self("SELECT * FROM usertokens"))
    
    def get_all_user_creds(self):
        """Returns all the user creds stored in teh database"""
        creds = {}
        for cred in self("SELECT * FROM usercreds"):
            creds[cred[0]] = dict(
                password= cred[1],
                suspended= cred[2],
                admin= cred[3])
        return creds



# Experimental tests
if __name__ == "__main__":
    load_dotenv()
    with Database() as db:
        """Execute some SQL for server testing"""
        
        print(db.get_user_token("aidzman"))
