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
    if (resp.url != undefined) {
        history.baseurl(resp.url).update();
        return;
    }
    /*if (resp.menu != undefined) {
        $("menubar").set("html", resp.menu);
        parse_menubar("menubar");
    }*/
    if (resp.listing != undefined) {
        $("#listing").html(resp.listing);
    }
    /*if ($defined(resp.navbar)) {
        $("navbar").set("html", resp.navbar);
        $$("#navbar a").addEvent("click", navbarcallback);
    }*/
}

