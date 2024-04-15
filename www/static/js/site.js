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

    // Make the search work
    $("#search").on("input",update_search)

    // Detect back / forward events
    $(window).on('popstate', update_content)

})

function update_search() {
    // Find the search term in the box
    let term = $("#search").val()

    // Get the full set of files
    let rowdata = $(".filerow")

    for (let i=0;i<rowdata.length; i++) {
        let filename = rowdata.eq(i).find(".filename").find("a").text()
        if (filename.includes(term)) {
            rowdata.eq(i).show()
        }
        else {
            rowdata.eq(i).hide()
        }
    }
}

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

function breadcrumb_click() {
    // They clicked on one of the breadcrumb items.  We need
    // to assemble a path from the current and previous 
    // breadcrumb objects and then update the content with
    // that.

    let thissection = $(this)[0]

    // We can't use the jquery object as it contains the prevobject
    // field which changes.  We need to pull out the underlying
    // js object.
    
    let newpath = ""

    let all_breadcrumbs = $(".breadcrumb")

    // We need to generate a path which is everything after the 
    // base site name

    // Test if they're clicking on the site name first
    if (!(all_breadcrumbs[0] === thissection)) {

        // Now append on any additional sections
        for (let i=1;i<all_breadcrumbs.length;i++) {
            newpath += all_breadcrumbs.eq(i).text()
            newpath += "/"
            if (all_breadcrumbs[i] === thissection) {
                break
            }
        }
    }

    let href = $(location).attr("href")

    href = href.substring(0,href.lastIndexOf(get_path()))

    href += newpath

    window.history.pushState('AutoSFTP', newpath, href);

    update_content()


}


function update_content () {
    // Get new file data

    // We want to make a breadcrumb out of the path
    let fullpath = ""
    let fullpath_sections = decodeURI(get_path()).split("/")

    fullpath_sections.unshift(get_username())

    for (let i=0;i<fullpath_sections.length;i++) {
        if (fullpath_sections[i]) {
            fullpath += "<span class='breadcrumb'>"+fullpath_sections[i]+"</span>"+"/"
        }
    }

    $("#sitename").html(fullpath)

    $(".breadcrumb").unbind()
    $(".breadcrumb").click(breadcrumb_click)


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

    // Reset the search
    $("#search").val("")

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

