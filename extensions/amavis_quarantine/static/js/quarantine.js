function updatehash(evt) {
  evt.stop();
  var url = $defined(this.get("href")) ? this.get("href") : "";
  current_anchor.parse_string(url, true).setparams(navparams);
  current_anchor.update();
}

function appendhash(evt) {
  evt.stop();
  location.hash += evt.target.get("href");
}

function updateparams(evt) {
  evt.stop();
  current_anchor.updateparams(evt.target.get("href"));
  current_anchor.update();
}

function actioncallback(resp) {
  $("listing").set("html", "");
  $("menubar").set("html", "");
  $("navbar").set("html", "");
  if (resp.status == "ok") {
    infobox.info(resp.respmsg);
    current_anchor.parse_string(resp.url, true).setparams(navparams);
    current_anchor.update(1);
  } else {
    infobox.error(resp.respmsg);
  }
}

function actionclick(evt) {
  new Request.JSON({
      url: evt.target.get("href"),
      onSuccess: actioncallback
  }).get();
}

function deleteclick(evt) {
    evt.stop();
    if (!confirm(gettext("Delete this message?"))) {
        return false;
    }
    actionclick(evt);
}

function releaseclick(evt) {
    evt.stop();
    if (!confirm(gettext("Release this message?"))) {
        return false;
    }
    actionclick(evt);
}

function viewmail_cs(evt) {
    evt.stop();
    var to = this.getFirst("td[name=to]");

    current_anchor.baseurl(this.get("id"));
    if ($defined(to)) {
        current_anchor.setparam("rcpt", to.get("html").trim());
    }
    current_anchor.update();
}

/*
 * Callback of the 'listing' action (the main screen)
 */
function listing_cb(resp) {
  updatelisting(resp);

  var tbl = new HtmlTable($("emails"), {
    useKeyboard: false,
    selectable: true
  });

  if ($("toggleselect")) {
    $("toggleselect").addEvent("click", function(evt) {
      if ($$("tr[class*=table-tr-selected]").length) {
        tbl.selectNone();
      } else {
        tbl.selectAll();
      }
    });
  }
  $$("a[name=selectmsgs]").addEvent("click", function(evt) {
    evt.stop();
    var type = evt.target.get("href");

    if (!$chk(type)) {
      $$("tr[class*=table-tr-selected]").each(function(item) {
        item.removeClass("table-tr-selected");
      });
      if ($("toggleselect").checked) {
        $("toggleselect").checked = false;
        tbl.selectNone();
      }
      return;
    }
    $$("td[name=type]").each(function(item) {
      if (item.get("html").trim() == type) {
        item.getParent().addClass("table-tr-selected");
      }
    });
  });
  $$("a[name=release]").addEvent("click", function(event) {
    if (!checkTableSelection(gettext("Release this selection?"))) {
      event.stop();
      return;
    }
    mysubmit(event, "release");
  });
  $$("a[name=delete]").addEvent("click", function(event) {
    if (!checkTableSelection(gettext("Delete this selection?"))) {
      event.stop();
      return;
    }
    mysubmit(event, "delete");
  });
  searchbox_init();
  init_sortable_columns();
  update_sortable_column();
  $$("tbody>tr").addEvent("dblclick", viewmail_cs);
}

/*
 * Callback of the 'viewmail' action
 */
function viewmail_cb(resp) {
  updatelisting(resp);
  $$("a[name=back]").addEvent("click", updatehash);
  $$("a[name=delete]").addEvent("click", deleteclick);
  $$("a[name=release]").addEvent("click", releaseclick);
  $$("a[name=viewmode]").addEvent("click", updateparams);
  setDivHeight("mailcontent", 5, 0);
}