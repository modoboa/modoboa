/*
 * Plugin : "Sieve filters"
 *
 * Javascript utilities
 */
var curscript = null;

/*
 * Remove a filter from a filters set.
 *
 */
function removefilter(evt) {
    evt.preventDefault();
    if (!confirm(gettext("Remove this filter?"))) {
        return;
    }
    var $this = $(this);

    $.ajax({
        url: $this.attr("href"),
        dataType: 'json'
    }).done(function(response) {
        histomanager.update(true);
        $("body").notify('success', response, 2000);
    });
}

/*
 * Handler listening for the "change" event on the filters sets list.
 */
function changefs(evt) {
    evt.preventDefault();
    histomanager.baseurl($(this).val()).update();
}

/*
 * Initializes buttons located inside the filters list
 */
function init_filters_list() {
    $("a[name=togglestate]").click(toggle_filter_state);
    $("a[name*=movefilter_]").click(move_filter);
    $("a[name=removefilter]").click(removefilter);
}

/*
 * Function called just after a new filters set has been loaded.
 *
 * It updates the middle DIV and initializes the user interface.
 */
function loadfs(response) {
    curscript = histomanager.getbaseurl();
    $("#curfset").val(curscript);
    $("#set_content").html(response.content);

    if ($("#filters_list") != undefined) {
        init_filters_list();
    }
    if ($("#fsetmenu").length) {
        $("#fsetmenu").remove();
    }
    $("#menu").after($(response.menu));
    $("a[name=activatefs]").click(activatefs);
    $("a[name=savefs]").click(savefs);
    $("a[name=removefs]").click(removefs);
}

/*
 * Common function to send a command that manipulates a filters set.
 *
 * (remove, activate)
 */
function send_command(cmd, extracb) {
    $.ajax({
        url: cmd,
        dataType: 'json'
    }).done(function(response) {
        if (extracb != undefined) {
            extracb(response);
        }
        if (!response.norefresh) {
            histomanager.update(true);
        }
        $("body").notify('success', response.respmsg, 2000);
    });
}

/*
 * Common utility used by filters set manipulation functions to
 * validate any new asked action. (activate, save, remove)
 */
function check_prereqs(evt, msg) {
  evt.preventDefault();
  if (!curscript) {
    return false;
  }
  if (msg != undefined && !confirm(msg)) {
    return false;
  }
  return true;
}

/*
 * Save the current filters set by applying the modifications to the
 * server.
 */
function savefs(evt) {
    if (!check_prereqs(evt, gettext("Save changes?"))) {
        return;
    }
    var $editor = $("#feditor");

    $.ajax({
        url: $editor.attr("action"),
        type: $editor.attr("method"),
        dataType: 'json',
        data: $editor.serialize()
    }).done(function(response) {
        $("body").notify('success', response.respmsg, 2000);
    });
}

/*
 * Remove the current filters set.
 *
 * On success, the user will be automatically redirected to the active
 * filters set.
 */
function removefs(evt) {
    if (!check_prereqs(evt, gettext("Remove filters set?"))) {
        return;
    }
    send_command($(this).attr("href"), function(response) {
        var $curfset = $("#curfset");

        $curfset.find("option[value='" + curscript + "']").remove();
        histomanager.baseurl(response.newfs, 1);
    });
}

/*
 * Activate the current filters set.
 */
function activatefs(evt) {
    var $this = $(this);

    if (!check_prereqs(evt, gettext("Activate this filters set?"))) {
        return;
    }
    send_command($this.attr("href"), function(response) {
        $("#curfset").find("option").each(function(index, element) {
            var $element = $(element);

            ($element.val() == curscript)
                ? $element.html(curscript + " (" + gettext("active") + ")")
                : $element.html($element.val());
        });
    });
}

/*
 * Enable/Disable a specific filter
 */
function toggle_filter_state(event) {
    var $this = $(this);

    event.preventDefault();
    $.ajax({
        url: $this.attr("href"),
        dataType: 'json'
    }).done(function(response) {
        $this.html(response.label);
        $this.attr("class", "");
        $this.addClass(response.color);
    });
}

function move_filter(event) {
    var $this = $(this);

    event.preventDefault();
    $.ajax({
        url: $this.attr('href'),
        dataType: 'json'
    }).done(function(response) {
        $("#set_content").html(response.content);
        init_filters_list();
    });
}

function filterset_created(data) {
    var name = data.url;
    var option = $('<option value="' + name + '">' + name + '</option>');
    var curfset = $(parent.document).find("#curfset");

    curfset.append(option);
    curfset.val(name);

    if (data.active) {
        curfset.find("option").each(function(index, element) {
            var $element = $(element);

            if ($element.val() == name) {
                $element.html(name + " (" + gettext("active") + ")");
            } else {
                $element.html($element.val());
            }
        });
    }
    histomanager.baseurl(data.url, 1).update(1);
}

function filtersetform_cb() {
    $("#newfiltersset").find("input").keypress(function(e) {
        if (e.which == 13) e.preventDefault();
    });
    $(".submit").on('click', function(e) {
        simple_ajax_form_post(e, {
            formid: "newfiltersset",
            reload_on_success: false,
            success_cb: filterset_created
        });
    });
}

/*
 * From here: specific functions used by the user-friendly form to
 * create/edit filters.
 */
function fetch_templates(url, container) {
    if (container) {
        return container;
    }
    var result;

    $.ajax({
        url: url,
        async: false,
        dataType: 'json'
    }).done(function(data) {
        result = data;
    });
    return result;
}
