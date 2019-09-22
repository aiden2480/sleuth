# Todo list
Tasks are categorised

## Next tasks
The nexts tasks I am currently working on
1. User settings page that includes a `logout of all sessions` button, `reset password` button and `change nickname` button
2. Admin commands such as `/kick`
3. Re-format database to handle storing `realname` and `nickname`

## main.py
- [ ] Fix the route order in `main.py`
- [ ] Ping clients from the server, not ping the server from the clients
    - Just use `multiprocessing` to make a `Process` to ping it every now and then

## Index page
- [ ] Make the navbar more mobile friendly
- [ ] Add reset password button

## User settings page
- [x] Needs to be created!
- [x] Create a `logout of all sessions` button somewhere which just deletes the user's token from the cache list

## In chat
- [x] Admin only commands such as `/kick` or smtn idk
    - [ ] Allow suspending from chat too
- [ ] Normal commands to show who is in chat
- [ ] If you're scrolling through the chat history and a message is sent, don't automatically scroll to bottom
- [ ] Don't scroll to top when a hash is changed (automatically, but maybe I should make it the bottom instead)
- [ ] The enter thingo from IDLE to copy a message into the input bar
- [ ] Able to send links in chat and they *actually link*
- [ ] Make different icons for user joining, user leaving etc for the notifications
- [x] Nicknames in chat
    - Sends a message in chat if someone changes their nickname
    - Save nicknames to database?
    - When a user joins the chat, send a message that says what everyones usernames/nicknames are
- [ ] Rate limiting for sending messaages
- [ ] Coloured text for messages
- [ ] Different channels to send messages in
- [x] Counter for who is active in the chat
- [ ] Profile pictures (probably inachieveable)
- [ ] Send pictures in chat
- [ ] Admin delete message command
- [ ] Fix the `invalid date` thing

## Admin
- [ ] Create a page which will eval SQL into the database

## Login page
- [ ] Fix margin on the login page to be 46px from the top
- [ ] Be able to pull `next` queries from the url
- [ ] Add a search paramater that says the login requires admin
    - After `next` thingo (above)

## Database
- [ ] `ALTER TABLE users` to set the column default for `nickname` and `token` to be `EMPTY`, not `NULL`
- [ ] Less strain on database and request time by not requesting the same data so much
    - Use a cache system
- [x] Completely redesign internal database structure
    - Just one table where the format is `id`, `name`, `pass`, `realname`, `nickname`, `token`

## Miscellaneous
- [ ] Higher quality for the bigger icons
- [ ] Upload chat logs to some external website or something
- [ ] Offline page auto pings server until online?
- [x] Profile pages (no idea what to put on em tho lol)
- [x] Fix the `no directory at` error thingo
- [ ] Use a proper colour picker because apparently piskel doesn't work properly

# Notes
- [ ] Empty Checkbox means not started yet
- [x] Marked checkbox means in progress
- Any indents are notes
