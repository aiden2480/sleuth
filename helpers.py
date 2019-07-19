import sqlite3

class Database(object):
    """Database interaction! Yay!"""

    # Inbuilt methods
    def __init__(self, databaseLocation= "assets/database.db"):
        self.databaseLocation = databaseLocation
    
    def __enter__(self):
        self.conn = sqlite3.connect(self.databaseLocation)
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.conn.close()
        del self

    def __call__(self, query, **context):
        """Execute raw SQL"""
        c = self.conn.cursor()
        try:
            result = c.execute(query.format(**context))
            self.conn.commit()
        except Exception as e:
            result = e
        return result
    
    # Custom methods
    def init_db(self, *, overwrite= True):
        """Initialise the database from a fresh start
        with all the setup required for the app.
        """#If param `overright` is `True`, """
        self("CREATE TABLE UserCreds (user VARCHAR(15), pass VARCHAR(15))")

    def create_user(self, user, _pass):
        """Registers a user into the database and returns said user.
        If the username already exists, a user will not be created"""
        p = self(f"SELECT * FROM UserCreds WHERE user='{user}'").fetchone()
        if p: return 1, p

        self(f"INSERT INTO UserCreds VALUES ('{user}', '{_pass}')")
        return 2, self(f"SELECT * FROM UserCreds WHERE user='{user}'").fetchone()
    
    def valid_login(self, user, _pass):
        """Attempts to 'login' to the database using the provided credentials
        If login succeeded, this will return `True`, else: `False`"""
        p = self(f"SELECT * FROM UserCreds WHERE user='{user}' AND pass='{_pass}'").fetchone()
        
        return bool(p)

if __name__ == "__main__":
    with Database() as db:
        #print(db.create_user("aidzman", "bacon"))
        print(db.valid_login("aidzman", "bacon"))
