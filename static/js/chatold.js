// The old chat script that I have just
// in case the new one breaks "somehow" (it will)
"use strict";

// Get cookies
function getCookieValue(value) {
    var b = document.cookie.match('(^|[^;]+)\\s*' + value + '\\s*=\\s*([^;]+)');
    return b ? b.pop() : '';
}

// Define Websocket URL
if (window.location.protocol == "https:") { // Secure
    var ws_url = `wss://${window.location.hostname}:${window.location.port}/websockets/${getCookieValue("token")}/`
} else { // Insecure
    var ws_url = `ws://${window.location.hostname}:${window.location.port}/websockets/${getCookieValue("token")}/`
}

// Set up variables
var container = document.getElementById("chat-container");
var socket = new WebSocket(ws_url);

// Socket Functions
socket.onmessage = function (event) {
    var element = document.createElement("div");
    var text = document.createTextNode(event.data);
    
    if (event.data.includes("joined the chat")) {
        element.setAttribute("style", "color: #258cd1");
    }
    if (event.data.includes("left the chat")) {
        element.setAttribute("style", "color: #258cd1");
    }
    
    element.appendChild(text);
    container.appendChild(element);
    scroll_to_bottom();
}

socket.onopen = function (event) {
    // We have successfully connected to the server and can enable the message box
    var message_sender = document.getElementById("message-field");
    message_sender.removeAttribute("disabled");
}

socket.onclose = function (event) {
    var element = document.createElement("div");
    var text = document.createTextNode(time()+" - Your connection with the server has been terminated. Please reload to rejoin the chat.");
    
    element.appendChild(text);
    element.setAttribute("style", "color: red");
    container.appendChild(element);
}

// Helper Functions
function time () {
    var today = new Date();
    return today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
}

function scroll_to_bottom () {
    window.scrollTo(0, document.body.scrollHeight);
}

function send_message() {
    var message_field = document.getElementById("message-field");
    var msg_content = message_field.value;

    // A bunch of checks required to send a message
    if (socket.readyState == socket.CONNECTING) {
        return boi_chill();
    }
    
    if (message_field.value.length > 150) {
        return too_many_chars();
    }

    if (message_field.value != "") {
        socket.send(msg_content);
        message_field.value = "";
    }
}

function too_many_chars() {
    var element = document.createElement("div");
    var chars = document.getElementById("message-field").value.length;
    var text = document.createTextNode(`${time()} - Your message could not be sent because it was over the 150 character limit (${chars} chars)`);

    element.appendChild(text);
    element.setAttribute("style", "color: red");
    container.appendChild(element);
    scroll_to_bottom();
}

function boi_chill() {
    var element = document.createElement("div");
    var text = document.createTextNode(`${time()} - The connection to the server is not yet active, please wait a few seconds or refresh.`);

    element.appendChild(text);
    element.setAttribute("style", "color: red");
    container.appendChild(element);
    scroll_to_bottom();
}
