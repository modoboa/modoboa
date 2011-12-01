/*
 * Class that implements a simple anchor based navigation system for
 * AJAX applications.
 */
var AnchorNavigation = new Class({
    Implements: [Options],

    options: {
        checkinterval: 300,
        defloadingtext: gettext("Loading..."),
        defloadingcolor: "gray",
        defcallback: null,
        spin_disabled: false,
        spin_target: undefined
    },

    initialize: function(deflocation, options) {
        this.setOptions(options);

        this.deflocation = deflocation;
        this.callbacks = {};
        this.params = $H();
        this.base = '';
        this.serialized = null;
        this.updatenext = true;
        this.reset_loading_infos();
        if (this.options.defcallback) {
            this.register_callback("default", this.options.defcallback);
            this.ca_id =
                this.check_anchor.bind(this).periodical(this.options.checkinterval);
        }
    },

    /*
     * Disable the spinner.
     */
    disable_spinner: function() {
        this.options.spin_disabled = true;
    },

    enable_spinner: function() {
        this.options.spin_disabled = false;
    },

    reset_loading_infos: function() {
        this.loading_message = this.options.defloadingtext;
        this.loading_color = this.options.defloadingcolor;
    },

    reset: function() {
        this.base = '';
        this.params.empty();
        return this;
    },

    parse_string: function(value, reset) {
        var splits = (value.charAt(0) == '#')
            ? value.substring(1).split('?') : value.split('?');

        if (splits.length == 0) {
            return this;
        }
        if (!$defined(reset)) {
            reset = false;
        }
        if (reset) {
            this.reset();
        }
        this.base = splits[0];

        if (this.base != "") {
            var re = new RegExp("/$");
            if (!this.base.match(re)) {
                this.base += '/';
            }
        }
        if (splits.length > 1) {
            var params = splits[1].split('&');
            for (var i = 0; i < params.length; i++) {
                var tmp = params[i].split('=');
                this.setparam(tmp[0], tmp[1]);
            }
        }
        return this;
    },

    from_string: function(value, reset) {
        this.parse_string(value);
        this.serialized = value;
        return this;
    },

    serialize: function() {
        var res = this.base;

        if (this.params.getLength() != 0) {
            res += "?" + this.params.toQueryString();
        }
        return res;
    },

    update: function(force, noupdate) {
        window.fireEvent("pageRefresh");
        location.hash = this.serialize();

        if (!$defined(noupdate)) {
            noupdate = false;
        }
        if (!noupdate) {
            if ($defined(force)) {
                this.force = force;
            }
        } else {
            this.updatenext = false;
        }
    },

    deleteParam: function(str) {
        this.params.erase(str);
    },

    updateparams: function(str) {
        if (str.charAt(0) == '?') {
            str = str.substring(1);
        }
        var elems = str.split('&');
        for (var i = 0; i < elems.length; i++) {
            this.setparamfromstring(elems[i]);
        }
        return this;
    },

    setparamfromstring: function(str) {
        var def = str.split('=');
        this.params.set(def[0], def[1]);
    },

    setparam: function(name, value) {
        this.params.set(name, value);
        return this;
    },

    setparams: function(params) {
        this.params.extend(params);
        return this;
    },

    getparam: function(name) {
        if (!this.params.has(name)) {
            return "";
        }
        return this.params.get(name);
    },

    baseurl: function(value, noreset) {
        if (!$defined(noreset) || noreset == 0) {
            this.reset();
        }
        this.base = value;
        var re = new RegExp("/$");
        if (!this.base.match(re)) {
            this.base += '/';
        }
        return this;
    },

    addbaseurl: function(value) {
        var newbase = this.base + value;
        return this.baseurl(newbase);
    },

    getbaseurl: function() {
        return this.base.substr(0, this.base.length - 1);
    },

    delparam: function(name) {
        if (!this.params.has(name)) {
            return false;
        }
        this.params.erase(name);
        return this;
    },

    register_callback: function(name, callback) {
        this.callbacks[name] = callback;
    },

    get_callback: function(name) {
        return this.callbacks[name];
    },

    set_default_callback: function(callback) {
        this.register_callback("default", callback);
        if (!$defined(this.ca_id)) {
            this.ca_id =
                this.check_anchor.bind(this).periodical(this.options.checkinterval);
        }
    },

    check_anchor: function() {
        if (this.serialized == location.hash && this.force == undefined) {
            return;
        }
        delete(this.force);

        this.from_string((location.hash != "") ? location.hash : "#" + this.deflocation);
        location.hash = this.serialized;

        if (!this.updatenext) {
            this.updatenext = true;
            return;
        }

        var query = this.serialized.substring(1);

        if (!this.options.spin_disabled) {
            var target = this.options.spin_target ? this.options.spin_target
                : document.body;
            $(target).spin({
                message: this.loading_message
            });
            /*infobox.show(this.loading_message, {
                profile: this.loading_color,
                spinner: true
            });*/
        }
        new Request.JSON({
            url: query,
            noCache : true,
            onSuccess: function(resp) {
                if (!this.options.spin_disabled) {
                    var target = this.options.spin_target ? this.options.spin_target
                        : document.body;
                    $(target).unspin();
                }
                if (resp.status == "ko") {
                    infobox.error(resp.respmsg);
                    return;
                }
                var callback = ($defined(resp.callback)) ? resp.callback : "default";
                this.callbacks[callback](resp);
                /*infobox.info(gettext("Done"));
                infobox.hide(1);*/
                this.reset_loading_infos();
            }.bind(this),
            onFailure: function(xhr) {
                $(document.body).set("html", xhr.responseText);
                $(document.body).setStyle("overflow", "auto");
            }
        }).get("json=1");
    }
});
