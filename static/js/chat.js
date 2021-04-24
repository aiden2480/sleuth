"use strict";

// Get cookies
function getCookieValue(value) {
    var b = document.cookie.match(`(^|[^;]+)\\s*${value}\\s*=\\s*([^;]+)`);
    return b ? b.pop() : "";
}

// Define Websocket URL
if (window.location.protocol == "https:") { // Secure
    var ws_url = `wss://${window.location.hostname}:${window.location.port}/websockets/${getCookieValue("sleuth_token")}/`
} else { // Insecure
    var ws_url = `ws://${window.location.hostname}:${window.location.port}/websockets/${getCookieValue("sleuth_token")}/`
}

// Set up variables
window.location.hash = "";
const load_time = new Date();
const production = !window.location.href.includes("localhost");

var container = document.getElementById("chat-container");
var socket = new WebSocket(ws_url);
var lastMessage = new Date();
var timeout = setInterval(function() {
    var t = lastMessage.getTime()/1000;
    var time9 = t + 60*9;
    var time930 = time9 + 30;
    var time10 = t + 60*10;
    var d = new Date().getTime()/1000;

    if (socket.readyState != socket.OPEN) {return;}
    if (time9 < d && time9+10 > d) {display_message("system", null, "You will be disconnected in one minute for inactivity", "orange");}
    if (time930 < d && time930+10 > d) {display_message("system", null, "You will be disconnected in thirty seconds for inactivity", "orange");}
    if (time10 < d) {return socket.close();}

    socket.send("");
}, 1000 * 10);

// Socket Functions
socket.onmessage = function(e) {
    console.log(JSON.parse(e.data));

    var colour = "default";
    var data = JSON.parse(e.data);
    var timestamp = new Date(data.timestamp * 1000);
    var text = data.content;

    if (data.type == "active_users") {
        return display_message("system", null, data.content, "orange", 0);
    }
    if (data.type == "message_delete") {
        return document.getElementById(data.content).remove();
    }
    if (data.author == "system") {
        colour = "#258cd1";
    }
    if (data.colour != undefined) {
        colour = data.colour;
    }

    display_message(data.author, data.nickname, text, colour, data.id, timestamp.toLocaleTimeString());
    show_notification(data);
}

socket.onopen = function(e) {
    console.log(e);
    // We have successfully connected to the server and can enable the message box
    var message_field = document.getElementById("message-field");
    message_field.removeAttribute("disabled");
    message_field.focus();
    message_field.setAttribute("placeholder", "Enter a message (max 200 chars)");
}

socket.onclose = function(e) {
    console.log(e);
    // Runs when the socket connection has been closed
    var message_field = document.getElementById("message-field");
    var element = document.createElement("div");
    var a = document.createElement("a");

    a.appendChild(document.createTextNode("reload"));
    a.setAttribute("href", "");
    a.setAttribute("style", "color: red");

    element.appendChild(document.createTextNode("You have been disconnected from the server, please "));
    element.setAttribute("title", `Message sent: ${time()}`);
    element.appendChild(a);
    element.appendChild(document.createTextNode(" to rejoin the chat."));

    if (e.reason != "") {
        element.appendChild(document.createTextNode(` Reason for disconnection: ${e.reason}`))
    }

    element.setAttribute("style", "color: red");
    container.appendChild(element);
    message_field.setAttribute("disabled", true);
    message_field.placeholder = "The connection to server has been closed, please reload the page.";
    window.document.title = `Disconnected • ${document.title}`;
    clearInterval(timeout); // Stop pinging the server
    scroll_to_bottom();
}

function send_message() {
    var message_field = document.getElementById("message-field");
    var msg_content = message_field.value.trim();

    if (msg_content.startsWith("!quit")) {
        socket.close();
    } else if (msg_content.startsWith("!clear")) {
        container.innerHTML = "";
        display_message("system", null, "Your chat logs have been cleared", "orange");
    } else if (msg_content == "") {
        // pass
    } else {
        socket.send(msg_content);
        window.lastMessage = new Date();
    }
    message_field.value = "";
}

function display_message(author, nickname, content, colour = "default", id = 0, timestamp=null) {
    // Displays a message in the chat
    var element = document.createElement("div");
    var bold = document.createElement("b");
    var authorx = document.createTextNode(nickname||author);
    var text = document.createTextNode(`: ${content}`);
    var p = `Message sent: ${timestamp||new Date().toLocaleTimeString()} by ${author}`;

    if (nickname) {
        p += ` as ${nickname}`
    }
    if (id > 0) {
        element.setAttribute("id", `${id}`);
    }
    if (colour != "default") {
        bold.setAttribute("style", `color: ${colour}`)
        element.setAttribute("style", `color: ${colour}`);
    }

    bold.appendChild(authorx);
    element.setAttribute("title", p);
    element.appendChild(bold);
    element.appendChild(text);
    container.appendChild(element);
    scroll_to_bottom();
}

// Helper Functions
function show_notification(messagedata) {
    // Checks
    if (Notification.permission != "granted") {return;}
    else if (messagedata.timestamp < load_time.getTime() / 1000) {}
    else if (document.hasFocus()) {}

    // Checks passed
    else {
        var notification = new Notification(`Message sent by ${messagedata.nickname||messagedata.author}`, {
            body: messagedata.content,
            icon: `${window.location.origin}/static/images/sleuth.png`,
            timestamp: new Date().getTime() / 1000,
        })

        // Set OnClick
        notification.onclick = function() {
            window.location.hash = messagedata.id;
            window.focus();
        }
    }
}

function time() {
    return new Date().toLocaleTimeString();
}

function scroll_to_bottom() {
    window.scrollTo(0, document.body.scrollHeight);
}

// Manage hashes
window.onhashchange = function () {
    var hash = document.getElementById("remove-hash");
    if (window.location.hash == "") {hash.hidden=true;}
    else {hash.hidden=false;}
    scroll_to_bottom();
}

// TODO: Properly make the custom context menu in chat.
/*window.addEventListener("contextmenu", e => {
    //e.preventDefault();
    //console.log(`You clicked: ${e.target.id} with ID ${e.target.id||null}`);
    if (e.target.parentElement.id == "chat-container" && e.target.id != "") {
        socket.send(`!delete ${e.target.id}`);
    }
});*/
