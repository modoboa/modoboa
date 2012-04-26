function domainform_cb() {
    $('input:text:visible:first').focus();
    $("#id_aliases").dynamic_input();
    $(".submit").one('click', function(e) {
        simple_ajax_form_post(e, {
            formid: "domform",
            error_cb: domainform_cb
        });
    });
    $("a[name=removeperm]").click(function(e) {
        var $tr = $(this).parent().parent();
        simple_ajax_request.apply(this, [e, {
            ok_cb: function(resp) {
                $tr.remove();
                if (!$("#domadmins").children("tr").length) {
                    $("#admins").html('<div class="alert alert-info">'
                        + gettext("No domain administrator defined") + "</div>");
                }
            }
        }]);
    });
}

function accountform_init() {
    $("#id_aliases").dynamic_input();
    $("#id_email").autocompleter({
        from_character: "@",
        choices: get_domains_list
    });
    $("#id_domains")
        .autocompleter({
            choices: get_domains_list
        })
        .dynamic_input();
}

function newaccount_cb() {
    $('input:text:visible:first').focus();
    accountform_init();
    $("#wizard").cwizard({formid: "newaccount_form"});
}

function editaccount_cb() {
    accountform_init();
    $('.submit').one('click', function(e) {
        simple_ajax_form_post(e, {
            formid: "accountform",
            error_cb: editaccount_cb
        });
    });
}

function aliasform_cb() {
    $("#id_email").autocompleter({
        from_character: "@",
        choices: get_domains_list
    });
    $("#id_recipients").dynamic_input();
    $(".submit").one('click', function(e) {
        simple_ajax_form_post(e, {
            formid: "aliasform",
            error_cb: aliasform_cb
        });
    });
}

function importform_cb() {
    $(".submit").one('click', function(e) {
        if ($("#id_sourcefile").attr("value") == "") {
            e.preventDefault();
            return;
        }
        $("#import_status").css("display", "block");
        $("#import_result").html("").removeClass("alert alert-error");
        $("form").submit();
    });
}

function importdone(status, msg) {
    $("#import_status").css("display", "none");
    if (status == "ok") {
        $("#modalbox").modal('hide');
        window.location.reload();
    } else {
        $("#import_result").addClass("alert alert-error");
        $("#import_result").html(msg);
        importform_cb();
    }
}