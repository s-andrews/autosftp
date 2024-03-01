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

    // Detect back / forward events
    $(window).on('popstate', update_content)

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


function process_login() {
    password = $("#password").val()
    update_content()
}

function update_content () {
    // Get new file data

    $("#sitename").text(get_username()+"/"+decodeURI(get_path()))


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
                    populate_file_table(content)
                }
            },
            error: function(message) {
                alert(message)
            }
        }
    )
}

function populate_file_table(data) {
    let table = $("#filestbody")
    table.empty()

    if (get_path()) {
        table.append(`<tr class="folderrow">
        <td><img src="/static/images/folder.svg"></td>
        <td class="filename">..</td>
        <td></td>
        </tr>`)    }

    for (let f in data) {
       let file = data[f]
    
       if (file["type"] == "folder") {
            table.append(`<tr class="folderrow">
                <td><img src="/static/images/folder.svg"></td>
                <td class="filename">${file["name"]}</td>
                <td></td>
            </tr>`)
       }
       else {
        table.append(`<tr class="filerow">
            <td><img src="/static/images/file.svg"></td>
            <td class="filename"><a href="/download/${get_username()}/${get_path()}/${file["name"]}">${file["name"]}</a></td>
            <td>${file["size"]}</td>
        </tr>`)
        }
    }

    // Register events
    $(".folderrow").unbind()
    $(".folderrow").click(folderclick)
}

function folderclick() {
    let path = get_path()
    let folder = $(this).find("td").eq(1).text()

    let newpath=path+folder+"/"

    let href = $(location).attr("href")

    href = href.substring(0,href.lastIndexOf(get_path()))

    href += newpath

    window.history.pushState('AutoSFTP', newpath, href);

    update_content()
}

