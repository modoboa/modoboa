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
    evt.stop();
    if (!confirm(gettext("Remove this filter?"))) {
        return;
    }
    new Request.JSON({
        url: this.get("href"),
        onSuccess: function(response) {
            if (response.status == "ok") {
                current_anchor.update(true);
                infobox.info(response.respmsg);
                infobox.hide(1);
            } else {
                infobox.error(response.respmsg);
            }
        }
    }).get();
}

/*
 * Handler listening for the "change" event on the filters sets list.
 */
function changefs(evt) {
    evt.stop();
    current_anchor.baseurl(this.get("value")).update();
}

/*
 * Initializes buttons located inside the filters list
 */
function init_filters_list() {
    SqueezeBox.assign($("filters_list").getElements('a[class=boxed]'), {
        parse: 'rel'
    });
    $$("a[name=togglestate]").addEvent("click", toggle_filter_state);
    $$("a[name*=movefilter_]").addEvent("click", move_filter);
}

/*
 * Function called just after a new filters set has been loaded.
 *
 * It updates the middle DIV and initializes the user interface.
 */
function loadfs(response) {
    curscript = current_anchor.getbaseurl();
    $("curfset").set("value", curscript);
    $("set_content").set("html", response.content);
    parse_menubar("fset_menu");
    if ($defined($("filters_list"))) {
        init_filters_list();
    }
    $$("a[name=removefilter]").addEvent("click", removefilter);
    $$("a[name=activatefs]").addEvent("click", activatefs);
    $$("a[name=savefs]").addEvent("click", savefs);
    $$("a[name=removefs]").addEvent("click", removefs);
}

/*
 * Common function to send a command that manipulates a filters set.
 *
 * (remove, activate)
 */
function send_command(cmd, extracb) {
    new Request.JSON({
        url: cmd,
        onSuccess: function(response) {
            if (response.status == "ko") {
                infobox.calcsize(300);
                infobox.error(response.respmsg);
            } else {
                if ($defined(extracb)) {
                    extracb();
                }
                if (!response.norefresh) {
                    current_anchor.update(true);
                }
                infobox.calcsize();
                infobox.info(response.respmsg);
                infobox.hide(2);
            }
        }
    }).get();
}

/*
 * Common utility used by filters set manipulation functions to
 * validate any new asked action. (activate, save, remove)
 */
function check_prereqs(evt, msg) {
  evt.stop();
  if (!curscript) {
    return false;
  }
  if ($defined(msg) && !confirm(msg)) {
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
    new Request.JSON({
        url: $("feditor").get("action"),
        method: $("feditor").get("method"),
        data: $("feditor").toQueryString(),
        onSuccess: function(response) {
            if (response.status == "ko") {
                infobox.calcsize(300);
                infobox.error(response.respmsg);
            } else {
                infobox.calcsize();
                infobox.info(response.respmsg);
                infobox.hide(2);
            }
        }
    }).send();
}

/*
 * Remove the current filters set.
 *
 * On success, the user will be automatically redirected to the active
 * filters set. (FIXME: what happens when there is no more script?)
 */
function removefs(evt) {
    if (!check_prereqs(evt, gettext("Remove filters set?"))) {
        return;
    }
    send_command(this.get("href"), function() {
        $("curfset").getElements("option[value=" + curscript + "]").destroy();
        if (!$("curfset").getElements("option[value=" + curscript + "]").length) {
            current_anchor.reset().update();
            location.reload();
        } else {
            current_anchor.reset();
        }
    });
}

/*
 * Activate the current filters set.
 */
function activatefs(evt) {
    if (!check_prereqs(evt, gettext("Activate this filters set?"))) {
        return;
    }
    send_command(
        this.get("href"),
        function() {
            $("curfset").getElements("option").each(function(item) {
                if (item.get("value") == curscript) {
                    item.set("html", curscript + " (" + gettext("active") + ")");
                } else {
                    item.set("html", item.get("value"));
                }
            });
        }
    );
}

function toggle_filter_state(event) {
    event.stop();
    new Request.JSON({
        url: this.get("href"),
        onSuccess: function(response) {
            if (response.status == "ok") {
                this.set("html", response.respmsg);
            } else {
                infobox.error(respmsg.respmsg);
            }
        }.bind(this)
    }).get();
}

function move_filter(event) {
    event.stop();
    new Request.JSON({
        url: this.get("href"),
        onSuccess: function(response) {
            $("filters_list").set("html", response.content);
            init_filters_list();
        }
    }).get();
}