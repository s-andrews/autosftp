$( document ).ready(function() {
    show_login()

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
    // Check the password they entered
}

function update_content () {
    // Get new file data
}

