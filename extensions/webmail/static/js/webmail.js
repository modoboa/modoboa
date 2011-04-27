/*
 * Globals
 */
var rtimer = null;

/*
 * Enables folders opening/closing
 *
 * Available for folders with subfolders.
 */
function init_folders_browsing() {
  $$("div[class*=clickbox]").addEvent("click", function(evt) {
    var parent = this.getParent();
    var ul = parent.getFirst("ul[name=" + parent.get("name") + "]");

    if (!$defined(ul)) {
      return;
    }
    if (ul.hasClass("hidden")) {
      this.removeClass("collapsed").addClass("expanded");
      ul.removeClass("hidden").addClass("visible");
    } else {
      this.removeClass("expanded").addClass("collapsed");
      ul.removeClass("visible").addClass("hidden");
    }
    evt.stop();
  });
}

/*
 * Select a particular folder
 */
function select_folder(obj) {
  $$("a[name=loadfolder]").each(function(item) {
    item.getParent().removeClass("selected");
    item.getParent().addClass("droppable");
  });
  obj.getParent().removeClass("droppable");
  obj.getParent().addClass("selected");

  $$(obj.getParents("ul[class*=hidden]")).each(function(item) {
    item.removeClass("hidden");
    item.addClass("visible");
    $$("li[name=" + item.get("name") + "]").each(function(item) {
      item.setStyle("background",
                    "url('" + static_url("pics/folder-open.png") + "') no-repeat");
    });
  });
}

/*
 * Callback of the 'viewmail' action
 */
function viewmail_cb(resp) {
  wm_updatelisting(resp, "hidden");
  $$("a[name=back]").addEvent("click", loadFolder);
  $$("a[name=reply]").addEvent("click", reply_loader);
  $$("a[name=replyall]").addEvent("click", replyall_loader);
  $$("a[name=forward]").addEvent("click", forward_loader);
  $$("a[name=delete]").addEvent("click", function(event) {
    var lnk = event.target;
    event.stop();
    simple_request(lnk.get("href"));
  });
  $$("a[name=activate_links]").addEvent("click", function(evt) {
    evt.stop();
    current_anchor.setparam("links", "1").update();
  });
  $$("a[name=disable_links]").addEvent("click", function(evt) {
    evt.stop();
    current_anchor.setparam("links", "0").update();
  });
  setDivHeight("mailcontent", 5, 0);
}

/*
 * Loader of the 'compose' action (called when the associated button
 * is clicked)
 */
function compose_loader(event) {
  event.stop();
  current_anchor.baseurl("compose").update();
}

function resize_window_callback(event) {
  setDivHeight("id_body", $("mailheader").getSize().y, 0);
}

/*
 * Callback of the 'compose' action
 */
function compose_callback(resp) {
  wm_updatelisting(resp);

  window.addEvent("resize", resize_window_callback);
  window.fireEvent("resize");

  var editormode = resp.editor;
  var editorid = "id_body";

  if (editormode == "html") {
    var instance = CKEDITOR.instances[editorid];
    if (instance) {
      CKEDITOR.remove(instance);
    }
    CKEDITOR.replace(editorid, {
      customConfig: static_url("js/editor_config.js"),
      height: $(editorid).getSize().y
    });
  }
  $$("a[name=back]")
    .removeEvents("click")
    .addEvent("click", loadFolder);
  $$("a[name=sendmail]")
    .removeEvents("click")
    .addEvent("click", function(evt) {
    evt.stop();
    $("composemail").set("send", {
      onSuccess: function(resp) {
        resp = JSON.decode(resp);
        if (resp.status == "ko") {
          get_callback("compose")(resp);

          if ($defined(resp.error)) {
            infobox.error(resp.error);
          }
          return;
        }
        current_anchor.parse_string(resp.url, true).setparams(navparams);
        current_anchor.update();
      }
    });
    if (editormode == "html") {
      CKEDITOR.instances[editorid].updateElement();
    }
    $("composemail").send();
  });
}

/*
 * Loader of the 'reply' action (called when the associated button
 * is clicked).
 */
function reply_loader(event) {
  event.stop();
  location.hash += event.target.get("href");
}

/*
 * Loader of the 'replyall' action (called when the associated button
 * is clicked).
 */
function replyall_loader(event) {
  event.stop();
  location.hash += event.target.get("href") + "?all=1";
}

/*
 * Loader of the 'forward' action (called when the associated button
 * is clicked).
 */
function forward_loader(event) {
  event.stop();
  location.hash += event.target.get("href");
}

/*
 * Onclick callback used to load the content of a particular
 * folder. (activated when clicking on a folder's name)
 */
function loadFolder(event, obj) {
  event.stop();
  if (!$defined(obj)) {
    obj = $(event.target);
  }
  current_anchor.parse_string(gethref(obj), true).setparams(navparams);
  current_anchor.update();
}

function foldercallback(event) {
  select_folder(event.target);
  loadFolder(event, event.target);
}

/*
 * Automatic folder listing refresh
 *
 * Called at a regular frequency to make an asynchronous request that
 * retrieves a folder's content (ie. mails)
 */
function refreshFolder() {
  var query = current_anchor.serialized.substring(1);

  clearInterval(rtimer);
  infobox.show(gettext("Reloading..."), {
    profile : "gray",
    spinner : true
  });
  new Request.JSON({url: query, noCache : true, onSuccess: function(resp) {
    var callback = ($defined(resp.callback)) ? resp.callback : "default";

    callbacks[callback](resp);
    infobox.info(gettext("Done"));
    infobox.hide(1);
  }}).get();
}

/*
 * Simple AJAX request
 *
 * Initialize the infobox with a loading message and wait for a JSON
 * encoded answer. The infobox is cleared by the request callback
 * function.
 */
function simple_request(url, params) {
  infobox.show(gettext("Waiting..."), {
    profile: "gray",
    spinner: true
  });
  new Request.JSON({
    url : url,
    onSuccess : function(response) {
      if (response.status == "ok") {
        if (!$defined(response.next)) {
          get_callback("folder")(response);
        }
        infobox.info(gettext("Done"));
        if ($defined(response.next)) {
          (function(response) {
            current_anchor.parse_string(response.next).update();
            select_folder($$("a[href=" + current_anchor.getbaseurl() + "]"));
          }).delay(500, this, response);
        } else {
          infobox.hide(1);
        }
      } else {
        infobox.error(response.error);
      }
    }
  }).get(params);
}