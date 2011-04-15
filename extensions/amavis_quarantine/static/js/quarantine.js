function updatehash(evt) {
  evt.stop();
  current_anchor.parse_string(evt.target.get("href"), true).setparams(navparams);
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
    infobox.info(resp.message);
  } else {
    infobox.error(resp.message);
  }
  infobox.hide(1);
  current_anchor.parse_string(resp.url, true).setparams(navparams);
  current_anchor.update(1);
}

function actionclick(evt) {
  evt.stop();
  new Request.JSON({
      url: evt.target.get("href"),
      onSuccess: actioncallback
  }).get();
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
  $$("tr").addEvent("dblclick", viewmail);
}

/*
 * Callback of the 'viewmail' action
 */
function viewmail_cb(resp) {
  updatelisting(resp);
  $$("a[name=back]").addEvent("click", updatehash);
  $$("a[name=delete]").addEvent("click", actionclick);
  $$("a[name=release]").addEvent("click", actionclick);
  $$("a[name=viewmode]").addEvent("click", updateparams);
  setDivHeight("mailcontent", 5, 0);
}