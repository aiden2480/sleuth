"use strict";
var ws_url = `ws://${window.location.hostname}:${window.location.port}${window.location.pathname}ws/`;
var container = document.getElementById("chat-container");
var socket = new WebSocket(ws_url);
socket.onmessage = function (event) {
    var element = document.createElement("div");
    var text = document.createTextNode(event.data);
    element.appendChild(text);
    container.appendChild(element);
}
socket.onclose = function (event) {
    var element = document.createElement("div");
    var text = document.createTextNode("Server closed for development, please refresh in a few seconds.");
    element.appendChild(text);
    element.setAttribute("style", "color:red;");
    container.appendChild(element);
}

function do_post() {
    var message_field_elem = document.getElementById("message-field");
    socket.send(message_field_elem.value);
}