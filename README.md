<style>
    * {
        color: #34475e;
        font-family: "Consolas";
        text-align: center;
    }
</style>

<div id="header" style="background-color: #2E4661">
    <h1 align="center" style="font-size: 300%; color: #EAE0C7">
        <img src="static/images/sleuth.png">
            SLEUTH CHAT APP
        <img src="static/images/sleuth.png">
    </h1>
</div>

<div id="badges" align="center">
    <a href="https://github.com/aiden2480/sleuth/commits/master">
        <img src="https://img.shields.io/github/last-commit/aiden2480/sleuth?color=%23d85200&style=for-the-badge" alt="GitHub last commit">
    </a>
    <a href="https://github.com/aiden2480/sleuth">
        <img src="https://img.shields.io/github/repo-size/aiden2480/sleuth?color=%2334475e&style=for-the-badge" alt="GitHub repo size">
    </a>
    <a href="https://github.com/aiden2480/sleuth">
        <img src="https://img.shields.io/github/commit-activity/m/aiden2480/sleuth?color=%23d85200&style=for-the-badge" alt="GitHub commits per month">
    </a>
    <a href="https://www.python.org/downloads/release/python-372/">
        <img src="https://img.shields.io/badge/python%20version-3.7.2-%2334475e?style=for-the-badge" alt="Python 3.7.2 homepage">
    </a>
    <a href="https://github.com/aiden2480/sleuth">
        <img src="https://img.shields.io/github/languages/top/aiden2480/sleuth?color=%23d85200&style=for-the-badge" alt="GitHub top language">
    </a>
    <a href="https://github.com/aiden2480/sleuth">
        <img src="https://img.shields.io/github/languages/count/aiden2480/sleuth?color=%232E4661&label=language%20count&style=for-the-badge" alt="GitHub language count">
    </a>
    <a href="TODO.md">
        <img src="https://img.shields.io/badge/todo%20list-todo.md-%23d85200?style=for-the-badge" alt="TODO.md file">
    </a>
    <a href="https://github.com/aiden2480/sleuth/stargazers">
        <img src="https://img.shields.io/github/stars/aiden2480/sleuth?color=%232E4661&label=stargazers&style=for-the-badge" alt="GitHub stargazers">
    </a>
    <a href="https://sleuth-chat.herokuapp.com">
        <img src="https://img.shields.io/badge/website-https%3A%2F%2Fsleuth--chat.herokuapp.com-%23d85200?style=for-the-badge" alt="Sleuth chat app">
    </a>
</div>

## Project description
A simple chat app I've created with user authentication to only allow certain people to join. I created it because [Discord](https://discordapp.com), the regular chat is blocked on school wifi and I couldn't find a decent chat that was unblocked, so I created my own 😉

## Inspiration
I created my chat off [this template](https://github.com/encukou/ws-chat), one of the only ones I could find that wasn't outdated.

## Config options
All config options are read from the environment using python's inbuilt method `os.getenv`. The current supported settings are;
<table>
    <tr>
        <th>Setting</th>
        <th>Description</th>
        <th>Default value</th>
    </tr>
    <tr>
        <td>DATABASE_URL</td>
        <td>The <code>postgres</code> formatted URL of the database to connect to</td>
        <td><b>Required</b> - no default</td>
    </tr>
    <tr>
        <td>HOST</td>
        <td>The host on which to run the server</td>
        <td><code>localhost</code></td>
    </tr>
    <tr>
        <td>PORT</td>
        <td>The port on which to run the server</td>
        <td><code>80</code></td>
    </tr>
    <tr>
        <td>PRINT_MESSAGES</td>
        <td>Specefies if the messages sent in chat should be logged in the console</td>
        <td><code>True</code></td>
    </tr>
    <tr>
        <td>MAX_CACHE_MESSAGE_LENGTH</td>
        <td>The maximum number of messages for the server to hold in the cache before deleting the oldest one</td>
        <td><code>0</code> (infinite)</td>
    </tr>
    <tr>
        <td>LOG_PINGS</td>
        <td>Specefies if keepalive pings from the client should be logged</td>
        <td><code>False</code></td>
    </tr>
    <tr>
        <td>DEVELOPMENT</td>
        <td>Specefies if the server is being used in a testing environment. This enables extra debug-only settings</td>
        <td><code>False</code></td>
    </tr>
    <tr>
        <td>COMMAND_PREFIX</td>
        <td>The prefix of the commands used in chat</td>
        <td><code>!</code></td>
    </tr>
    <tr>
        <td>NICKNAME_COOLDOWN</td>
        <td>The number of seconds a user must wait between each change before being able to change it again</td>
        <td><code>0</code> (No cooldown)</td>
    </tr>
</table>
