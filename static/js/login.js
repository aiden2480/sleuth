var searches = new URL(location.href).searchParams;

function check_params() {
    // Searches the search params for username
    var login_field = document.getElementsByName("user")[0];
    var username = searches.get("username");
    var d = document.forms[0];

    if (username) {login_field.value = username;}
    d.action = `/login${window.location.search}`;
}

function detect_error() {
    var errordiv = document.getElementById("error-div");
    var incorrectcreds = document.getElementById("incorrect-creds")
    if (searches.has("incorrect")) {
        incorrectcreds.style.display = "block";
        errordiv.style.height = "7%"
    }
}