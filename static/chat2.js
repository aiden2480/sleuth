// Set up variables
"use strict";
var ws_url = `ws://${window.location.hostname}:${window.location.port}${window.location.pathname}ws/`;
var container = document.getElementById("chat-container");
var socket = new WebSocket(ws_url);

// Socket Functions
socket.onmessage = function (event) {
    var element = document.createElement("div");
    
    if (event.data.type == "user_join") {
        element.setAttribute("style", "color: #3498db");
        var fmt = `${time()} - system: ${event.data.user} joined the chat`;
    } elif (event.data.type == "user_leave") {
        element.setAttribute("style", "color: #3498db");
        var fmt = `${time()} - system: ${event.data.user} left the chat`;
    } else {
        var fmt = `${time()} - ${event.data.author}: ${event.data.content}`;
    }
    
    element.appendChild(document.CreateTextNode(fmt));
    container.appendChild(element);
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

// Other Functions
function time () {
    var today = new Date();
    return today.getHours() + ":" + today.getMinutes() + ":" + today.getSeconds();
}

function send_message() {
    var message_field_elem = document.getElementById("message-field");
    
    if (message_field_elem.value != "") {
        socket.send({"type": "message", "content": message_field_elem.value});
        message_field_elem.value = "";
    }
}
