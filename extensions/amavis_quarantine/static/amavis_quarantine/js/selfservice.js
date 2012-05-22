function send_action(e, message) {
    var $link = $(e.target);

    e.preventDefault();
    if (!confirm(message)) {
        return;
    }
    $.ajax({
        url: $link.attr("href"),
        dataType: 'json',
        success: function(data) {
            if (data.status == "ok") {
                $("body").notify("success", data.respmsg, 2000);
            } else {
                $("body").notify("error", data.respmsg);
            }
        }
    });
}

function release(e) {
    send_action(e, gettext("Release this message?"));
}

function remove(e) {
    send_action(e, gettext("Delete this message?"));
}

$(document).ready(function() {
    $("#listing").css({
        top: $("#menubar").outerHeight() + 10
    });
    $(document).on("click", "a[name=release]", release);
    $(document).on("click", "a[name=delete]", remove);
});