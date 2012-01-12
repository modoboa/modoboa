/*
 * Collection of functions that are accessible to every page.
 */

/*
 * Simple function that redirect ajax requests to the login page if
 * the status code received with a response is equal to 278.
 */
function ajax_login_redirect() {
    if (this.status != 278) {
        return;
    }
    var params = "?next=" + window.location.pathname;

    window.location.href =
        this.xhr.getResponseHeader("Location").replace(/\?.*$/, params);
}

/*
 * Simple wrapper around Request.JSON. We just ensure that
 * redirections are correctly catched. (on session timeout for
 * example)
 */
Request.JSON.mdb = new Class({
    Extends: Request.JSON,

    options: {
        onComplete: ajax_login_redirect,
        onFailure: function(xhr) {
            $(document.body).setStyle("overflow", "auto");
            $(document.body).set("html", xhr.responseText);
        }
    }
});