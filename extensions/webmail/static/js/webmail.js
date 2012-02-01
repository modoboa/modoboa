var Webmail = new Class({
    Implements: [Options],

    /*
     * Default values for options
     */
    defaults: {
        refreshRate: 0,
        modify_url: "",
        delete_url: "",
        move_url: "",
        submboxes_url: ""
    },

    /*
     * Constructor
     */
    initialize: function(options) {
        this.setOptions(options);

        this.rtimer = null;
        this.editorid = "id_body";

        this.init_folders_buttons();
        this.init_folders_browsing();

        /* FIXME: à faire uniquement pour le mode pushState */
        /*this.init_emails_table();*/

        current_anchor.disable_spinner();
        current_anchor.register_callback("listmailbox",
                                         this.listmailbox_callback.bind(this));
        current_anchor.register_callback("viewmail", this.viewmail_callback.bind(this));
        current_anchor.register_callback("compose", this.compose_callback.bind(this));
        current_anchor.register_callback("reply", this.compose_callback.bind(this));
        current_anchor.register_callback("replyall", this.compose_callback.bind(this));
        current_anchor.register_callback("forward", this.compose_callback.bind(this));

        this.gspinner = new Spinner("document.body", {
            message: gettext("Loading, please wait..."),
            'class': "spinner-noop"
        });
        this.gspinner.addEvent("hide", function(target) {
            this.gspinner.destroy();
            delete(this.gspinner);
            current_anchor.enable_spinner();
        }.bind(this));
        this.gspinner.show();
    },

    send_mark_request: function(evt) {
      evt.stop();
      if (!this.emails_table._selectedRows.length) {
        return;
      }
      var ids = new Array();

      this.emails_table._selectedRows.each(function(item, index) {
          ids.include(item.get("id"));
      });
      this.simple_request(evt.target.get("href"), {
          ids : ids.join()
      }, function(response) {
          if (response.action == "read") {
              this.emails_table._selectedRows.removeClass("unseen");
          } else {
              this.emails_table._selectedRows.addClass("unseen");
          }
          /*
           * MAJ de l'affichage du nombre de messages non lus
           * (faire fonction à part)
           */
      }.bind(this));
    },

    /*
     * Open/Close the menu containing folder buttons
     */
    toggle_folder_buttons: function(evt) {
        var parent = evt.target.getParent();
        var fdname = parent.getFirst("a[name=loadfolder]").get("href");

        this.fdmenu.toggle(evt.target, fdname);
        evt.stop();
    },

    /*
     * Initializes the misc. buttons available to manipulate folders.
     */
    init_folders_buttons: function() {
        $$("li[class*=clickable]").removeEvents();

        $$("a[name=loadfolder]").addEvent("click", this.listmailbox_loader.bind(this));

        SqueezeBox.assign($("folders").getElements('a[class=boxed]'), {
            parse: 'rel'
        });

        this.fdmenu = new FdMenu({
            modify_url: this.options.modify_url,
            delete_url: this.options.delete_url
        });

        $$("img[class*=footer]")
            .addEvent("click", this.toggle_folder_buttons.bind(this));
    },

    /*
     * Open/Close a mailbox with children
     */
    toggle_mbox_state: function(div, ul) {
        if (ul.hasClass("hidden")) {
            div.removeClass("collapsed").addClass("expanded");
            ul.removeClass("hidden").addClass("visible");
        } else {
            div.removeClass("expanded").addClass("collapsed");
            ul.removeClass("visible").addClass("hidden");
        }
    },

    /*
     * Inject new mailboxes under a given parent in the tree.
     */
    inject_mailboxes: function(parent, mboxes) {
        var ul = new Element("ul", {
            name: parent.get("name"),
            'class': "hidden"
        }).inject(parent);

        for (var i = 0; i < mboxes.length; i++) {
            var mbname = mboxes[i].name;
            var li = new Element("li", {
                name: mbname,
                'class': "droppable folder"
            }).inject(ul);
            var img = new Element("img", {
                'class': "footer",
                src: static_url("pics/go-down.png")
            }).inject(li);
            var link = new Element("a", {
                name: "loadfolder",
                'class': "block",
                href: mbname
            }).inject(li);
            var parts = mbname.split(".");
            var displayname = parts[parts.length - 1];

            if (mboxes[i].unseen != undefined) {
                link.addClass("unseen");
                link.set("html", displayname + " (" + mboxes[i].unseen + ")");
            } else {
                link.set("html", displayname);
            }

            link.addEvent("click", this.listmailbox_loader.bind(this));
            img.addEvent("click", this.toggle_folder_buttons.bind(this));
        }
        this.init_draggables();
        this.toggle_mbox_state(parent.getFirst("div"), ul);
    },

    /*
     * Download sub-mailboxes from the server
     */
    get_mailboxes: function(parent) {
        new Request.JSON({
            url: this.options.submboxes_url,
            onSuccess: function(resp) {
                if (resp.status == "ko") {
                    return;
                }
                this.inject_mailboxes(parent, resp.mboxes);
            }.bind(this)
        }).get({topmailbox: parent.get("name")});
    },

    /*
     * Enables folders opening/closing
     *
     * Available for folders with subfolders.
     */
    init_folders_browsing: function() {
        $$("div[class*=clickbox]").addEvent("click", function(evt) {
            var div = evt.target;
            var parent = div.getParent();
            var ul = parent.getFirst("ul[name=" + parent.get("name") + "]");

            if (ul == undefined) {
                this.get_mailboxes(parent);
                return;
            }
            this.toggle_mbox_state(div, ul);
            evt.stop();
        }.bind(this));
    },

    /*
     * Select a particular folder
     */
    select_folder: function(obj) {
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
                item.setStyle(
                    "background",
                    "url('" + static_url("pics/folder-open.png") + "') no-repeat"
                );
            });
        });
    },

    /*
     * Automatic folder listing refresh
     *
     * Called at a regular frequency to make an asynchronous request that
     * retrieves a folder's content (ie. mails)
     */
     refresh_folder: function() {
         var query = current_anchor.serialized.substring(1);

         clearInterval(this.rtimer);
         infobox.show(gettext("Reloading..."), {
             profile : "gray",
             spinner : true
         });
         new Request.JSON({url: query, noCache : true, onSuccess: function(resp) {
             var callback = ($defined(resp.callback)) ? resp.callback : "default";

             current_anchor.get_callback(callback)(resp);
             infobox.info(gettext("Done"));
             infobox.hide(1);
         }}).get();
     },

    init_automatic_refresh: function() {
        this.rtimer = this.refresh_folder
            .periodical(this.options.refreshRate);
    },

    /*
     * Emails table initialization.
     */
    init_emails_table: function() {
        this.emails_table = new HtmlTable($("emails"), {
            selectable: true,
	    shiftForMultiSelect: true
        }).addEvents({
            rowFocus: function(tr) {
	        clearInterval(this.rtimer);
	    }.bind(this),
	    rowUnfocus: function(tr) {
	        if (this.emails_table._selectedRows.length == 0) {
                    this.init_automatic_refresh();
	        }
	    }.bind(this)
        });

        /* The IE way for disabling default selection */
        /* Actually it doesn't work :p */
        $$("tbody>tr").set("unselectable", "on");

        if ($("toggleselect")) {
            $("toggleselect").addEvent("click", function(evt) {
	        if (evt.target.checked) {
	            this.emails_table.selectAll();
	        } else {
	            this.emails_table.selectNone();
	        }
                evt.stopPropagation();
	    }.bind(this));
        }

        init_sortable_columns();
        update_sortable_column();

        this.init_draggables();

        $$("tbody>tr").addEvent("dblclick", this.viewmail_loader);
    },

    /*
     * Drag & Drop feature
     */
    init_draggables: function(pattern) {
        if (this.dragobjs == undefined) {
            this.dragobjs = new Array();
        } else {
            this.dragobjs.each(function(item) {
                item.detach();
                delete(item);
            });
            this.dragobjs = new Array();
        }

        $$("td[class*=draggable]").each(function(item) {
            var pid = item.getParent().get("id");

            this.dragobjs[pid] = item.makeDraggable({
	        droppables: ".droppable"
	    }).addEvents({
	        beforeStart: this.bstart_dragging.bind(this),
	        start: this.start_dragging.bind(this),
                enter: this.enter_droppable,
	        leave: this.leave_droppable,
                drop: this.drop_element.bind(this),
	        cancel: this.cancel_dragging.bind(this)
	    });
        }.bind(this));
    },


    /*
     * 'before start' event callback
     */
    bstart_dragging: function(item) {
        var dragobj = this.dragobjs[item.getParent().get("id")];
        var block = new Element("div", {id: "draggeditems", 'class': "dragbox"})
	    .setStyles({
                top : dragobj.element.getCoordinates()['top'],
		left : dragobj.element.getCoordinates()['left']
            }).inject(document.body);

	block.store("parent", dragobj.element);
        dragobj.element = block;
	clearInterval(this.rtimer);
    },

    start_dragging: function(item, event) {
        var tr = event.target.getParent();

	if (!this.emails_table.isSelected(tr)) {
	    this.emails_table.selectNone();
	    this.emails_table.selectRow(tr);
	}
	item.set("html", "Moving " + this.emails_table._selectedRows.length + " messages");
	item.setStyle("display", "block");
    },

    enter_droppable: function(item, droppable) {
	droppable.addClass("dragging");
    },

    leave_droppable: function(item, droppable) {
	droppable.removeClass("dragging");
    },

    restore_parent: function(item) {
	var parent = item.retrieve("parent");
        var drag = this.dragobjs[parent.getParent().get("id")];

	drag.element = parent;
        this.init_automatic_refresh();
    },

    drop_element: function(item, droppable, event) {
	item.dispose();
        if (!droppable) {
	    this.restore_parent(item);
	    return;
        }
        droppable.removeClass("dragging");
        var dest = gethref(droppable.getFirst("a"));
        var msgset = new Array();

        this.emails_table._selectedRows.each(function(item, index) {
	    msgset.include(item.get("id"));
	});
        this.simple_request(this.options.move_url, {
            msgset : msgset.join(),
            to : dest
        });
    },

    cancel_dragging: function(item) {
	item.dispose();
	this.restore_parent(item);
    },

    /*
     * Bottom left quota bar initialisation.
     */
    init_quota_bar: function() {
        this.quota_pb = new ProgressBar({
            container: $("quotabox"),
            startPercentage: 0,
            boxID: "box",
            percentageID: "perc",
            displayText: true,
            displayID: "quotatext"
        });
    },

    /*
     *
     */
    page_update: function(response) {
        if (this.gspinner) {
            this.gspinner.hide();
        }
        updatelisting(response);
    },

    /*
     * Webmail actions start here
     */

    /*
     * Onclick callback used to load the content of a particular
     * folder. (activated when clicking on a folder's name)
     */
    _listmailbox_loader: function(event, obj) {
        event.stop();
        if (obj == undefined) {
            obj = $(event.target);
        }
        current_anchor.reset().setparams({
           action: "listmailbox",
           name: gethref(obj)
        }).update();
    },

    listmailbox_loader: function(event) {
        this.select_folder(event.target);
        this._listmailbox_loader(event, event.target);
    },

    /*
     * Callback for 'folder' action
     */
    listmailbox_callback: function(resp) {
        window.removeEvents("resize");
        this.page_update(resp);
        if (resp.menu != undefined) {
            searchbox_init();
            $$("a[name=compose]").addEvent("click", this.compose_loader);
            $$("a[name=mark-read]")
                .addEvent("click", this.send_mark_request.bind(this));
            $$("a[name=mark-unread]")
                .addEvent("click", this.send_mark_request.bind(this));
            $$("a[name=fdaction]").addEvent("click", function(evt) {
                this.simple_request(evt.target.get("href"), {});
                evt.stop();
            }.bind(this));
        }
        this.init_emails_table();
    },

    /*
     * Loader of the 'viemmail' action
     */
    viewmail_loader: function(evt) {
        evt.stop();
        current_anchor.reset().setparams({
            action: "viewmail",
            mailid: this.get("id")
        }).update();
    },

    /*
     * Callback of the 'viewmail' action
     */
    viewmail_callback: function(resp) {
        /*wm_updatelisting(resp, "hidden");*/
        this.page_update(resp);

        //$$("a[name=back]").addEvent("click", this._listmailbox_loader);
        $$("a[name=reply]").addEvent("click", this.reply_loader);
        $$("a[name=replyall]").addEvent("click", this.replyall_loader);
        $$("a[name=forward]").addEvent("click", this.forward_loader);
        $$("a[name=delete]").addEvent("click", function(event) {
            var lnk = event.target;
            event.stop();
            this.simple_request(lnk.get("href"));
        }.bind(this));
        $$("a[name=activate_links]").addEvent("click", function(evt) {
            evt.stop();
            current_anchor.setparam("links", "1").update();
        });
        $$("a[name=disable_links]").addEvent("click", function(evt) {
            evt.stop();
            current_anchor.setparam("links", "0").update();
        });
        setDivHeight("mailcontent", 5, 0);
    },

    /*
     * Loader of the 'compose' action (called when the associated button
     * is clicked)
     */
    compose_loader: function(event) {
        event.stop();
        current_anchor.reset().setparam("action", this.get("href")).update();
    },

    /*
     * Loader of the 'reply' action (called when the associated button
     * is clicked).
     */
    reply_loader: function(event) {
        event.stop();
        location.hash += event.target.get("href");
    },

    /*
     * Loader of the 'replyall' action (called when the associated button
     * is clicked).
     */
    replyall_loader: function(event) {
        event.stop();
        location.hash += event.target.get("href") + "?all=1";
    },

    /*
     * Loader of the 'forward' action (called when the associated button
     * is clicked).
     */
    forward_loader: function(event) {
        event.stop();
        location.hash += event.target.get("href");
    },

    /*
     * Resize the current editor on page resizing.
     */
    resize_window_callback: function(event) {
        CKEDITOR.instances[this.editorid]
            .resize("100%", $("body_container").getSize().y);
    },

    /*
     * Callback of the 'compose' action.
     *
     * It is also shared with other similar actions : reply, forward.
     */
    compose_callback: function(resp) {
        //wm_updatelisting(resp);
        this.page_update(resp);

        window.addEvent("resize", this.resize_window_callback.bind(this));

        var editormode = resp.editor;

        if (editormode == "html") {
            var instance = CKEDITOR.instances[editorid];
            if (instance) {
                CKEDITOR.remove(instance);
            }
            CKEDITOR.replace(editorid, {
                customConfig: static_url("js/editor_config.js")
            });
            CKEDITOR.on("instanceReady", function(evt) {
                this.resize_window_callback();
            }.bind(this));
        }
        if (resp.id) {
            current_anchor.setparam("id", resp.id).update(0, 1);
        }
        $("attachments").addEvent("click", function(evt) {
            SqueezeBox.open(this.get("name"), {
                handler: "iframe",
                size: {x: 350, y: 400},
                closeBtn: false
            });
        });

        /*$$("a[name=back]")
            .removeEvents("click")
            .addEvent("click", this._listmailbox_loader);*/
        $$("a[name=sendmail]")
            .store("editormode", editormode)
            .removeEvents("click")
            .addEvent("click", this.sendmail_callback.bind(this));
    },

    /*
     * Callback of the 'sendmail' action.
     */
    sendmail_callback: function(evt) {
        evt.stop();
        infobox.show(gettext("Sending..."), {
            profile : "gray",
            spinner : true
        });
        disable_link(this);
        $("composemail").set("send", {
            onSuccess: function(resp) {
                resp = JSON.decode(resp);
                if (resp.status == "ko") {
                    current_anchor.get_callback("compose")(resp);
                    if ($defined(resp.respmsg)) {
                        infobox.error(resp.respmsg);
                    }
                    enable_link(this, sendmail_callback);
                    return;
                }
                current_anchor.parse_string(resp.url, true).setparams(navparams);
                current_anchor.update();
                this.eliminate("editormode");
            }.bind(this)
        });
        if (this.retrieve("editormode") == "html") {
            CKEDITOR.instances[editorid].updateElement();
        }
        $("composemail").send();
    },


    /*
     * Simple AJAX request
     *
     * Initialize the infobox with a loading message and wait for a JSON
     * encoded answer. The infobox is cleared by the request callback
     * function.
     */
    simple_request: function(url, params, callback) {
        infobox.show(gettext("Waiting..."), {
            profile: "gray",
            spinner: true
        });
        params["json"] = "1";
        new Request.JSON({
            url : url,
            onSuccess : function(response) {
                if (response.status == "ok") {
                    if (response.next == undefined) {
                        if (callback != undefined) {
                            callback(response);
                        } else {
                            current_anchor.get_callback("listmailbox")(response);
                        }
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
                    infobox.error(response.respmsg);
                }
            }
        }).get(params);
    }
});


/*
 * Globals
 */
var rtimer = null;
var editorid = "id_body";

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
    CKEDITOR.instances["id_body"].resize("100%", $("body_container").getSize().y);
}

/*
 * Callback of the 'sendmail' action.
 */
function sendmail_callback(evt) {
    evt.stop();
    infobox.show(gettext("Sending..."), {
        profile : "gray",
        spinner : true
    });
    disable_link(this);
    $("composemail").set("send", {
        onSuccess: function(resp) {
            resp = JSON.decode(resp);
            if (resp.status == "ko") {
                current_anchor.get_callback("compose")(resp);
                if ($defined(resp.respmsg)) {
                    infobox.error(resp.respmsg);
                }
                enable_link(this, sendmail_callback);
                return;
            }
            current_anchor.parse_string(resp.url, true).setparams(navparams);
            current_anchor.update();
            this.eliminate("editormode");
        }.bind(this)
    });
    if (this.retrieve("editormode") == "html") {
        CKEDITOR.instances[editorid].updateElement();
    }
    $("composemail").send();
}

/*
 * Callback of the 'compose' action
 */
function compose_callback(resp) {
  wm_updatelisting(resp);

  var editormode = resp.editor;

  if (editormode == "html") {
    window.addEvent("resize", resize_window_callback);
    var instance = CKEDITOR.instances[editorid];
    if (instance) {
      CKEDITOR.remove(instance);
    }
    CKEDITOR.replace(editorid, {
      customConfig: static_url("js/editor_config.js")
    });
    CKEDITOR.on("instanceReady", function(evt) {
        resize_window_callback();
    });
  }
  if (resp.id) {
      current_anchor.setparam("id", resp.id).update(0, 1);
  }
  $("attachments").addEvent("click", function(evt) {
      SqueezeBox.open(this.get("name"), {
          handler: "iframe",
          size: {x: 350, y: 400},
          closeBtn: false
      });
  });

  $$("a[name=back]")
    .removeEvents("click")
    .addEvent("click", loadFolder);
  $$("a[name=sendmail]")
    .store("editormode", editormode)
    .removeEvents("click")
    .addEvent("click", sendmail_callback);
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
  new Request.JSON.mdb({
      url: query,
      noCache : true,
      onSuccess: function(resp) {
          var callback = ($defined(resp.callback)) ? resp.callback : "default";

          current_anchor.get_callback(callback)(resp);
          infobox.info(gettext("Done"));
          infobox.hide(1);
      }
  }).get();
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
  new Request.JSON.mdb({
    url : url,
    onSuccess : function(response) {
      if (response.status == "ok") {
        if (!$defined(response.next)) {
          current_anchor.get_callback("folder")(response);
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
        infobox.error(response.respmsg);
      }
    }
  }).get(params);
}