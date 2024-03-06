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

    // Action when they log out
    $("#logout").click(logout)

    // Action for a new site
    $("#newsite").click(show_newsite)

    // Action for finishing a new site
    $("#finishnewsite").click(finish_new_site)

    // Update days on change of validity
    $("#validfor").on("input",function() {console.log("Changed");$("#validdays").text($("#validfor").val())})

})

function show_newsite() {
    $("#sitename").val("")
    $("#validfor").val(1)
    $("#validdays").text(1)
    $("#nopassword").prop("checked",false)
    $("#allowupload").prop("checked",false)
    $("#editsiteid").val("")

    $("#creatededit").text("Create New")
    $("#finishnewsite").text("Create Site")
    $("#newsitediv").modal("show")

}

function write_site_table(site_data) {
    let table = $("#sitestbody")

    table.empty()

    if (!site_data.length) {
        table.append("<tr><td colspan=9>No Sites Yet</th></th>")
    }

    for (i in site_data) {
        let site = site_data[i]

        let anonsymbol = "&cross;"
        let uploadsymbol = "&cross;"

        if (site["anonymous_https"] == "true") {
            anonsymbol = "&check;"
        }

        if (site["https_upload"] == "true") {
            uploadsymbol = "&check;"
        }


        table.append(`<tr data-id=${site["_id"]["$oid"]}>
        <td>${site["name"]}</td>
        <td>${site["username"]}</td>
        <td>${site["password"]}</td>
        <td>${site["days"]} day(s)</td>
        <td>${anonsymbol}</td>
        <td>${uploadsymbol}</td>
        <td><button class="btn btn-success btn-sm siteopen">Open</button></td>
        <td><button class="btn btn-primary btn-sm siteedit">Edit</button></td>
        <td><button class="btn btn-danger btn-sm sitedelete">Delete</button></td>

      </tr>`)

    }

    //  Reregister the button actions
    $(".siteopen").unbind()
    $(".siteopen").click(open_site)

    $(".siteedit").unbind()
    $(".siteedit").click(edit_site)

    $(".sitedelete").unbind()
    $(".sitedelete").click(delete_site)

}

function open_site () {
    // Get the username of the site
    let sitename = $(this).parent().parent().find("td").eq(1).text()

    window.open("/sites/"+sitename+"/","_blank")

}

function edit_site() {
    $("#editsiteid").val($(this).parent().parent().data("id"))
    $("#sitename").val($(this).parent().parent().find("td").eq(0).text())
    $("#validfor").val($(this).parent().parent().find("td").eq(3).text().split(" ")[0])
    $("#validdays").text($(this).parent().parent().find("td").eq(3).text().split(" ")[0])
    $("#nopassword").prop("checked",$(this).parent().parent().find("td").eq(4).text()=="✓")
    $("#allowupload").prop("checked",$(this).parent().parent().find("td").eq(5).text()=="✓")


    $("#createedit").text("Edit")
    $("#finishnewsite").text("Edit Site")
    $("#newsitediv").modal("show")

}

function delete_site() {

    let id = $(this).parent().parent().data("id")

    if (!confirm("Are you SURE you want to delete this site and all data?\nYou cannot undo this operation")) {
        return
    }

    $.ajax(
        {
            url: "delete_site",
            method: "POST",
            data: {
                session: session,
                id: id
            },
            success: function() {
                refresh_sites()
            },
            error: function(message) {
                alert("Failed to delete site")
            }
        }
    )
}


function finish_new_site() {
    let name=$("#sitename").val()
    let validfor=$("#validfor").val()
    let anonymous = $("#nopassword").prop("checked")
    let upload = $("#allowupload").prop("checked")

    // If this is an edit not a new site then editsiteid
    // will be populated
    let siteid = $("#editsiteid").val()

    $.ajax(
        {
            url: "create_site",
            method: "POST",
            data: {
                session: session,
                name: name,
                days: validfor,
                anonymous: anonymous,
                upload: upload,
                siteid: siteid
            },
            success: function() {
                $("#newsitediv").modal("hide")
                refresh_sites()
            },
            error: function(message) {
                $("#newsitediv").modal("hide")
                alert("Failed to create/edit site")
            }
        }
    )
}


function refresh_sites() {
    // Update the table of sites for this user
    $.ajax(
        {
            url: "site_list",
            method: "POST",
            data: {
                session: session
            },
            success: function(site_list) {
                write_site_table(site_list)
            },
            error: function(message) {
                alert("Failed to get list of sites")
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

    session = Cookies.get("autosftp_session_id")
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

                    refresh_sites()

                },
                error: function(message) {
                    console.log("Existing session didn't validate")
                    session = ""
                    Cookies.remove("autosftp_session_id")
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
    Cookies.remove("autosftp_session_id")
    $("#maincontent").hide()

    $("#logindiv").modal("show")
}




function process_login() {
    let username = $("#username").val()
    let password = $("#password").val()

    // Clear the password so they can't do it again
    $("#password").val("")
    $("#login").prop("disabled",true)
    $("#username").prop("disabled",true)
    $("#password").prop("disabled",true)


    // Add a spinner so they know it's trying!
    $("#login").html(`<span class="spinner-border spinner-border-sm" role="status" aria-hidden="true"></span> Checking`)
    

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

                Cookies.set("autosftp_session_id", session, { secure: false, sameSite: 'strict' })
                $("#login").text("Log In")
                $("#login").prop("disabled",false)
                $("#username").prop("disabled",false)
                $("#password").prop("disabled",false)
            
                show_login()
            },
            error: function(message) {
                $("#login").prop("disabled",false)
                $("#username").prop("disabled",false)
                $("#password").prop("disabled",false)
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

