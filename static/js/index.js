// Handle notifications
var check_notification_status = function () {
    document.getElementById("notification-status").innerText = Notification.permission;
    var description = document.getElementById("notification-description");
    
    if (Notification.permission == "granted") {description.innerText = "You will receive notifications in chat when a message is sent and you do not have focus on the window."};
    if (Notification.permission == "denied") {description.innerText = "You will not receive any kind of chat notifications.\nYou will have to manually enable this in your browser settings."};
    if (Notification.permission == "default") {description.innerText = "You have not yet accepted notifications and so will not receive any until you do."};

    var l = Notification.permission;
    if (Notification.permission == "default") {
        var button = document.createElement("button");
        button.innerHTML = "Request notifications";
        button.onclick = function(){Notification.requestPermission().then(function(r) {
            if (r != l) {window.location.reload()};
            });
        };
        document.body.appendChild(button);
    };
};

// Stoof for installing as a PWA
window.addEventListener("load", window), (e) => {
    const pwadiv = document.getElementById("pwa-install-div");
    pwadiv.style.display = "none";
};

window.addEventListener("beforeinstallprompt", (e) => {
    const pwadiv = document.getElementById("pwa-install-div");
    const addBtn = document.getElementById("pwa-install-button");
    // Prevent Chrome 67 and earlier from automatically showing the prompt
    //e.preventDefault();
    // Stash the event so it can be triggered later.
    deferredPrompt = e;
    // Update UI to notify the user they can add to home screen
    pwadiv.style.display = "block";

    addBtn.addEventListener("click", (e) => {
        // Show the prompt
        deferredPrompt.prompt();
        // Wait for the user to respond to the prompt
        deferredPrompt.userChoice.then((choiceResult) => {
            if (choiceResult.outcome === "accepted") {
                console.log("[PWA] User accepted the A2HS prompt");
                // hide our user interface that shows our A2HS button
                pwadiv.style.display = "none"
            } else {
                console.log("[PWA] User dismissed the A2HS prompt");
            }
            deferredPrompt = null;
        });
    });
});
