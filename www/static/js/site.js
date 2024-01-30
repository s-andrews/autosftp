var password = ""


$( document ).ready(function() {
    update_content()

    // Action when they log in
    $("#login").click(process_login)
    $("#password").keypress(function(e){
        if(e.keyCode == 13){
            process_login();
        }
    });

})

function get_username() {
    // Work out the username from the current href
    let sections = $(location).attr("href").split("/")

    for (i in sections) {
        if (sections[i] == "sites") {
            return(sections[parseInt(i)+1])
        }
    } 
}

function get_path () {
    // Work out the username from the current href
    let sections = $(location).attr("href").split("/")

    for (i in sections) {
        if (sections[i] == "sites") {
            return((sections.slice(parseInt(i)+2)).join("/"))
        }
    } 
}

function show_login() {
    // Check if this is a protected site and show login
    // otherwise populate the content
}

function process_login() {
    password = $("#password").val()
    update_content()
}

function update_content () {
    // Get new file data

    // We'll call for the content for the currently 
    // selected folder.  If they've previously entered
    // a password we'll send that with the request
    // and if the request fails for a missing password
    // then we'll just clean up and show the login 
    // prompt

    $.ajax(
        {
            url: "/get_content",
            method: "POST",
            data: {
                username: get_username(),
                path: get_path(),
                password: password

            },
            success: function(content) {
                if (content=="password") {
                    // Hide any content, show the password dialog
                    $("#maincontent").hide()
                    $("#logindiv").modal("show")
                }
                else {
                    $("#logindiv").modal("hide")
                    $("#maincontent").show()
                }
            },
            error: function(message) {
                alert(message)
            }
        }
    )

}

