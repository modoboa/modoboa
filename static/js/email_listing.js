/*
 * Shared functions between the webmail and the quarantine plugin.
 *
 */

function navbarcallback(event) {
  event.stop();
  current_anchor.setparams(navparams);
  current_anchor.parse_string($(event.target).getParent().get("href")).update();
}

function updatelisting(resp) {
    if ($defined(resp.url)) {
        current_anchor.baseurl(resp.url).update();
        return;
    }
    if ($defined(resp.menu)) {
        $("menubar").set("html", resp.menu);
        parse_menubar("menubar");
    }
    if ($defined(resp.listing)) {
        $("listing").set("html", resp.listing);
    }
    if ($defined(resp.navbar)) {
        $("navbar").set("html", resp.navbar);
        $("navbar").getChildren("a").addEvent("click", navbarcallback);
    }
}

