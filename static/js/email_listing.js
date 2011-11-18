/*
 * Shared functions between the webmail and the quarantine plugin.
 *
 */

function navbarcallback(event) {
    event.stop();
    current_anchor.reset()
        .setparams(navparams)
        .updateparams(this.get("href"))
        .update();
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
        $$("#navbar a").addEvent("click", navbarcallback);
    }
}

