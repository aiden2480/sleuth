<style>* {color: #34475e; font-family: "Consolas"}</style>
<div id="header" style="background-color: #2E4661">
    <h1 align="center" style="font-size: 300%; color: #EAE0C7">
        <img src="static/images/sleuth.png">
            SLEUTH TODO LIST
        <img src="static/images/sleuth.png">
    </h1>
</div>

## Notes
- [ ] Empty Checkbox means not started yet
- [x] Marked checkbox means in progress
    - Any indents are notes

## Next tasks
The tasks I am focusing on from the list below
1.  User settings page that includes a `logout of all sessions` button, `reset password` button and `change nickname` button
2. `aiohttp_session`/`aiohttp_auth` support for user login sessions, *not* for in chat
    - Though maybe I should make it for in chat too 🤔
3. Ping chat clients from the server, not the server from the client

## main.py
- [ ] Fix the route order in `main.py`
- [ ] Add `aiohttp_session` support
- [ ] Ping clients from the server, not ping the server from the clients
    - Just use `multiprocessing` to make a `Process` to ping it every now and then
- [ ] Be able to detect spam using a custom function and not send the message if it was spam and not sent by an admin. The same function to rate-limit messages too
- [ ] Detect if a user does not have focus on a page and send a message to the server saying they are idle if so

## Index page
- [ ] Make the navbar more mobile friendly
- [ ] Add reset password button

## User settings page
- [x] Needs to be created!
- [x] Create a `logout of all sessions` button somewhere which just deletes the user's token from the cache list

## In chat
- [ ] If you're scrolling through the chat history and a message is sent, don't automatically scroll to bottom
- [ ] Don't scroll to top when a hash is changed (automatically, but maybe I should make it the bottom instead)
- [ ] The enter thingo from IDLE to copy a message into the input bar
- [ ] Able to send links in chat and they *actually link*
- [ ] Make different icons for user joining, user leaving etc for the notifications
- [ ] Rate limiting for sending messaages
- [ ] Coloured text for messages
- [ ] Different channels to send messages in
- [ ] Profile pictures (probably inachieveable)
- [ ] Send pictures in chat
- [ ] Fix the `invalid date` thing

## Admin
- [ ] Create a page which will eval SQL into the database

## Login page
- [ ] Fix margin on the login page to be 46px from the top
- [ ] Add a search paramater that says the login requires admin

## Database
- [ ] `ALTER TABLE users` to set the column default for `nickname` and `token` to be `EMPTY`, not `NULL`
- [ ] Less strain on database and request time by not requesting the same data so much
    - Use a cache system

## Miscellaneous
- [ ] Higher quality for the bigger icons
- [ ] Upload chat logs to some external website or something
- [ ] Offline page auto pings server until online?
- [x] Profile pages (no idea what to put on em tho lol)
- [x] Fix the `no directory at` error thingo
- [ ] Use a proper colour picker because apparently piskel doesn't work properly
