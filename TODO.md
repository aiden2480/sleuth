# Todo list
**Completed by next update**
- [x] Admin only commands such as `/kick` or smtn idk
- [x] Ping clients from the server, not ping the server from the clients
    - Just use `multiprocessing` to make a `Process` to ping it every now and then
- [x] Make an `add to home screen` button (that would be cool)
    - omfg this is so fucking annoying it doesn't even work lol
- [x] Fix images
- [x] Make the navbar more mobile friendly
- [x] Fix the route order in `main.py`

**Other objectives**
- [ ] Get rid of all the argparse bs in `main.py` and instead make it read from env
- [ ] Rate limiting for sending messaages
- [ ] **Make it fkn mobile friendly reeeeee**
- [ ] Make links *link* (create a `href` element to hold them)
- [ ] Coloured text in chat
- [x] For the login route, be able to pull `next` queries from the url
- [ ] Block ship names
- [ ] Different channels to send messages in
- [ ] Counter for who is active in the chat
- [ ] Profile pictures (probably inachieveable)
- [ ] Send pictures in chat
- [ ] Less strain on database and request time by not requesting the same data so much
- [ ] Profile pages (no idea what to put on em tho lol)
- [ ] Make a typing indicator?

# Completed
**A list of all the objectives completed this commit**
- [x] Kpop detector (if a message has kpop it won't be sent and the sender will be kicked)
- [x] Once the connection has terminated, grey out the message input box
- [x] Display a message if someone tries to send a message while the websocket is still connecting
    - Just disabled the input field ez lol
- [x] Add a character limit in chat of 200
- [x] Fix glitch where messages at the bottom of the screen are hidden by the message box sender
    - Just creating a div element the same size should do it
- [x] List of names to usernames on the homepage (eg `father` - `Jack`)
- [x] Change window title to smtn if you're disconnected in chat
- [x] Style up username + password fields on the `/login` page
- [x] Fix message word wrap in chat
- [x] Fix the notifications
- [x] Create a settings page which will just incorporate notification settings lol
    - It's on the homepage now bish

# Notes
- [ ] Empty Checkbox means not started yet
- [x] Marked checkbox means in progress
- Any indents are notes
