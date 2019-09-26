# sleuth chat app
A simple chat app I've created with user authentication to only allow certain people to join. The website link is currently at https://sleuth-chat.herokuapp.com so navigate there ;)

## Todo list
The todo list is in the [TODO.md](TODO.md) file, but any suggestions can be opened in the issues tab

## Config options
All config options are read from the environment using `os.getenv`. The current supported settings are:
1. `HOST` :: The host on which to run the server :: Default `None`
2. `PORT` :: The port on which to run the server :: Default `80`
3. `PRINT_MESSAGES` :: Specefies if the messages sent in chat should be logged in the console :: Default `True`
4. `DATABASE_URL` :: The postgres-formatted URL of the database to connect to :: **No default, this *must* be set**
5. `MAX_CACHE_MESSAGE_LENGTH` :: The maximum number of messages for the server to hold in the cache before deleting the oldest one :: Default `0` (infinite)
6. `LOG_PINGS` :: Specefies if keepalive pings from the client should be logged :: Default `False`
7. `DEVELOPMENT` :: Specefies if the server is being used in a testing environment :: Default `False`
8. `COMMAND_PREFIX` :: The prefix of the commands used in chat :: Default `"!"`
9. `NICKNAME_COOLDOWN` :: The number of seconds a user must wait between each change before being able to change it again :: Default `0` (No cooldown)
