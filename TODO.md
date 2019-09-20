# Todo list
Tasks are categorised

## main.py
- [ ] Fix the route order in `main.py`
- [ ] Ping clients from the server, not ping the server from the clients
    - Just use `multiprocessing` to make a `Process` to ping it every now and then

## Index page
- [ ] Make the navbar more mobile friendly
- [ ] Create a `logout of all sessions` button somewhere which just deletes the user's token from the cache list
- [ ] Add reset password button

## User settings page
- [x] Needs to be created!

## In chat
- [x] Admin only commands such as `/kick` or smtn idk
    - [ ] Allow suspending from chat too
- [ ] If you're scrolling through the chat history and a message is sent, don't automatically scroll to bottom
- [ ] Don't scroll to top when a hash is changed (automatically, but maybe I should make it the bottom instead)
- [ ] The enter thingo from IDLE to copy a message into the input bar
- [ ] Able to send links in chat and they *actually link*
- [ ] Make different icons for user joining, user leaving etc for the notifications
- [ ] Nicknames in chat
    - Sends a message in chat if someone changes their nickname
    - Save nicknames to database?
    - When a user joins the chat, send a message that says what everyones usernames/nicknames are
- [ ] Rate limiting for sending messaages
- [ ] Coloured text for messages
- [ ] Different channels to send messages in
- [ ] Counter for who is active in the chat
- [ ] Profile pictures (probably inachieveable)
- [ ] Send pictures in chat

## Login page
- [ ] Fix margin on the login page to be 46px from the top
- [ ] Be able to pull `next` queries from the url
- [ ] Add a search paramater that says the login requires admin
    - After `next` thingo (above)

## Database
- [x] Less strain on database and request time by not requesting the same data so much
    - Use a cache system
- [ ] Completely redesign internal database structure
    - Just one table where the format is `id`, `name`, `pass`, `realname`, `nickname`, `token`

## Miscellaneous
- [ ] Higher quality for the bigger icons
- [ ] Upload chat logs to some external website or something
- [ ] Offline page auto pings server until online?
- [ ] Profile pages (no idea what to put on em tho lol)
- [x] Fix the `no directory at` error thingo

# Notes
- [ ] Empty Checkbox means not started yet
- [x] Marked checkbox means in progress
- Any indents are notes
