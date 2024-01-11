var session = ""

$( document ).ready(function() {
    show_login()

    // Action when they log in
    $("#login").click(process_login)
    $("#password").keypress(function(e){
        if(e.keyCode == 13){
            process_login();
        }
    });

    // Pressme button
    $("#pressme").click(button_pressed)

    // Action when they log out
    $("#logout").click(logout)

})


function button_pressed() {
    $.ajax(
        {
            url: "get_user_data",
            method: "POST",
            data: {
                session: session
            },
            success: function(user_data) {
                write_user_data(user_data)
            },
            error: function(message) {
                alert("Failed to get user data")
            }
        }
    )
}

function write_user_data(user_data) {
    $("#user_details_name").html(user_data["name"])
    $("#user_details_username").html(user_data["username"])
    $("#user_details_email").html(user_data["email"])

}

function show_login() {

    // Check to see if there's a valid session ID we can use

    session = Cookies.get("groupactivity_session_id")
    if (session) {
        // Validate the ID
        $.ajax(
            {
                url: "validate_session",
                method: "POST",
                data: {
                    session: session,
                },
                success: function(usersname) {
                    $("#logindiv").modal("hide")

                    $("#maincontent").show()

                    $("#loginname").text(usersname)

                },
                error: function(message) {
                    console.log("Existing session didn't validate")
                    session = ""
                    Cookies.remove("groupactivity_session_id")
                    $("#logindiv").modal("show")
                    show_login()
                }
            }
        )
    }
    else {
        $("#logindiv").modal("show")
    }
}

function logout() {
    session_id = ""
    Cookies.remove("groupactivity_session_id")
    $("#maincontent").hide()

    $("#logindiv").modal("show")
}




function process_login() {
    let username = $("#username").val()
    let password = $("#password").val()

    // Clear the password so they can't do it again
    $("#password").val("")

    $.ajax(
        {
            url: "login",
            method: "POST",
            data: {
                username: username,
                password: password
            },
            success: function(session_string) {
                $("#loginerror").hide()
                session = session_string

                Cookies.set("groupactivity_session_id", session, { secure: false, sameSite: 'strict' })
                show_login()
            },
            error: function(message) {
                $("#login").text("Login Failed")
                $("#login").removeClass("btn-primary")
                $("#login").addClass("btn-danger")
                setTimeout(function(){
                    $("#login").text("Log In")
                    $("#login").removeClass("btn-danger")
                    $("#login").addClass("btn-primary")
                    },2000)
            }
        }
    )
}

