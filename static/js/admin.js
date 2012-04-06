function domainform_cb() {
    $('input:text:visible:first').focus();
    $("#id_aliases").dynamic_input();
    $(".submit").one('click', function(e) {
        simple_ajax_form_post(e, domainform_cb);
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
    $("#wizard").cwizard();
}

function editaccount_cb() {
    accountform_init();
    $('.submit').one('click', function(e) {
        simple_ajax_form_post(e, {
            error_cb: editaccount_cb
        });
    });
}

function dlistform_cb() {
    $("#id_email").autocompleter({
        from_character: "@",
        choices: get_domains_list
    });
    $("#id_recipients").dynamic_input();
    $(".submit").one('click', function(e) {
        simple_ajax_form_post(e, {
            error_cb: dlistform_cb
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
        $("form").submit();
    });
}

function importdone(status, msg) {
    $("#import_status").css("display", "none");
    if (status == "ok") {
        $("#modalbox").modal('hide');
        window.location.reload();
    } else {
        $("#import_result").html("");
        $(".modal-header").notify({top_position: 10});
        $(".modal-header").notify('error', msg);
    }
}