var searches = new URL(location.href).searchParams;

function check_params() {
    // Searches the search params for username
    var login_field = document.getElementsByName("user")[0];
    var username = searches.get("username");
    if (username) {login_field.value = username;}
}

function detect_error() {
    var errordiv = document.getElementById("error-div");
    var incorrectcreds = document.getElementById("incorrect-creds")
    if (searches.has("incorrect")) {
        incorrectcreds.style.display = "block";
        errordiv.style.height = "7%"
    }
}