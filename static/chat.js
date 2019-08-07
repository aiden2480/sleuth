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
        element.setAttribute("style", "color: #258cd1"); // #3498db");
    }
    if (event.data.includes("left the chat")) {
        element.setAttribute("style", "color: #258cd1"); // #3498db");
    }
    
    element.appendChild(text);
    container.appendChild(element);
    window.scrollTo(0, document.body.scrollHeight);
}

socket.onopen = function (event) {
    return; // This is only called when a client joins
    var element = document.createElement("div");
    var text = document.createTextNode(time()+" - Server started!");

    element.appendChild(text);
    element.setAttribute("style", "color: limegreen");
    container.appendChild(element);
}

socket.onclose = function (event) {
    var element = document.createElement("div");
    var text = document.createTextNode(time()+" - Your connection with the server has been terminated. Please try again later.");
    
    element.appendChild(text);
    element.setAttribute("style", "color: red");
    container.appendChild(element);
}

// Helper Functions
function time () {
    var today = new Date();
    return today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
}

function send_message() {
    var message_field_elem = document.getElementById("message-field");
    
    if (message_field_elem.value != "") {
        socket.send(message_field_elem.value);
        message_field_elem.value = "";
    }
}
