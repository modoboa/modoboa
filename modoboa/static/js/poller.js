/*
 * Simple poller plugin.
 *
 * Sends a request at a given frequency.
 */
var Poller = function(url, options) {
    this.initialize(url, options);
};

Poller.prototype = {
    constructor: Poller,

    defaults: {
        interval: 2000,
        success_cb: null,
        error_cb: null
    },

    initialize: function(url, options) {
        this.url = url;
        this.options = $.extend({}, this.defaults, options);
        this.running_request = false;
        this.paused = false;
        this.reset();
    },

    reset: function() {
        if (!this.paused) {
            this.tid = setTimeout($.proxy(this.send_request, this), this.options.interval);
        }
    },

    pause: function() {
        this.paused = true;
        if (!this.tid) {
            return;
        }
        clearTimeout(this.tid);
    },

    resume: function() {
        if (!this.paused) {
            return;
        }
        this.paused = false;
        this.reset();
    },

    send_request: function() {
        var poller = this;
        var args = "";

        if (this.options.args != undefined) {
            args = "?";
            if (typeof this.options.args === "function") {
                args += this.options.args();
            } else {
                args += this.options.args;
            }
        }
        this.running_request = true;
        $.ajax({
            url: this.url + args,
            dataType: 'json',
            global: false
        }).done(function(data) {
            poller.running_request = false;
            if (poller.options.success_cb) {
                poller.options.success_cb(data);
            }
            poller.reset();
        }).fail(function(jqxhr) {
            var data = $.parseJSON(jqxhr.responseText);
            $("body").notify("error", data);
            if (poller.options.error_cb) {
                poller.options.error_cb(data);
            }
        });
    }
};