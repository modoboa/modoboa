/**
 * Creates an instance of History.
 *
 * @constructor
 * @this {History}
 * @param {dictionary} options - instance options
 */
var History = function(options) {
    this.options = $.extend({}, this.defaults, options);
    this.callbacks = {};
    this.base = '';
    this.serialized = null;
    this.updatenext = true;
    this.load_params();
    if (this.options.defcallback) {
        this.register_callback("default", this.options.defcallback);
        this.check_id =
            setInterval($.proxy(this.check, this), this.options.checkinterval);
    }
};

History.prototype = {
    constructor: History,

    defaults: {
        checkinterval: 300,
        deflocation: null,
        defcallback: null
    },

    /**
     * Return the encoded hash part of the URL (some browsers like FF
     * automatically decode the location.hash variable).
     */
    get_raw_hash: function() {
        var parts = window.location.href.split('#');
        if (parts.length > 1) {
            return parts[1];
        }
        return "";
    },

    load_params: function() {
        var rawqs = this.get_raw_hash();

        if (!rawqs || rawqs.indexOf('?') == -1) {
            this.params = {};
            return;
        }
        var tmp = rawqs.split('?');

        rawqs = (tmp.length == 1) ? tmp[0] : tmp[1];
        this.params = parse_qs(rawqs.split('&'));
    },

    paramslength: function() {
        return Object.keys(this.params).length;
    },

    reset: function() {
        this.base = "";
        this.params = {};
        return this;
    },

    parse_string: function(value, reset) {
        var splits = (value.charAt(0) == '#') ?
            value.substring(1).split('?') : value.split('?');

        if (splits.length === 0) {
            this.base = this.options.deflocation;
            return this;
        }
        if (reset === undefined) {
            reset = false;
        }
        if (reset) {
            this.reset();
        }

        if ((this.base = splits[0]) !== "") {
            var re = new RegExp("/$");
            if (!this.base.match(re)) {
                this.base += '/';
            }
        }
        if (splits.length > 1) {
            var params = splits[1].split('&');
            for (var i = 0; i < params.length; i++) {
                var tmp = params[i].split('=');
                this.setparam(tmp[0], tmp[1], false);
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
        var args = "";

        if (this.paramslength() !== 0) {
            args += "?";
            $.each(this.params, function(key, value) {
                if (args != "?") {
                    args += "&";
                }
                args += key + "=" + value;
            });
        }
        return res + args;
    },

    /**
     * Update the current location.
     *
     * @param {boolean} force - force the update
     * @param {boolean} noupdate - disable the next update
     */
    update: function(force, noupdate) {
        location.hash = this.serialize();

        if (noupdate === undefined) {
            noupdate = false;
        }
        if (!noupdate) {
            if (force) {
                this.force = force;
            }
        } else {
            this.updatenext = false;
        }
    },

    /**
     * Check if a parameter is present.
     *
     * @param {string} name - name of the parameter
     * @return {boolean} true if parameter is present, false otherwise
     */
    hasparam: function(name) {
        return this.params[name] !== undefined;
    },

    /**
     * Retrieve a parameter.
     *
     * @param {string} name - name of the parameter
     * @return {string} the parameter's value (URI decoded)
     */
    getparam: function(name, defvalue) {
        if (this.params[name] === undefined) {
            return (defvalue !== undefined) ? defvalue : undefined;
        }
        return decodeURIComponent(this.params[name]);
    },

    /**
     * Set a parameter.
     *
     * @param {string} name - name of the parameter
     * @param {string} value - parameter's value
     * @param {boolean} encode - URI encode the parameter if true
     * @return {History}
     */
    setparam: function(name, value, encode) {
        if (encode === undefined || encode) {
            this.params[name] = encodeURIComponent(value);
        } else {
            this.params[name] = value;
        }
        return this;
    },

    /**
     * Set several parameters.
     *
     * @param {Object} params - a dictionary of parameters
     * @return {Object} - History instance
     */
    setparams: function(params) {
        $.each(params, $.proxy(this.setparam, this));
        return this;
    },

    updateparams: function(str) {
        if (str.charAt(0) == '?') {
            str = str.substring(1);
        }
        var elems = str.split('&');
        for (var i = 0; i < elems.length; i++) {
            var pdef = elems[i].split('=');
            this.setparam(pdef[0], pdef[1]);
        }
        return this;
    },

    /**
     * Delete a parameter.
     *
     * @param {string} name - name of the parameter
     * @return {History}
     */
    delparam: function(name) {
        if (this.params[name] === undefined) {
            return this;
        }
        delete(this.params[name]);
        return this;
    },

    baseurl: function(value, noreset) {
        if (noreset === undefined || noreset === 0) {
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
        return decodeURIComponent(this.base.substr(0, this.base.length - 1));
    },

    register_callback: function(name, callback) {
        this.callbacks[name] = callback;
    },

    get_callback: function(name) {
        return this.callbacks[name];
    },

    set_default_callback: function(callback) {
        this.register_callback("default", callback);
        if (this.ca_id === undefined) {
            this.ca_id =
                setInterval($.proxy(this.check, this), this.options.checkinterval);
        }
    },

    check: function() {
        var rawhash = this.get_raw_hash();

        if (this.serialized === rawhash && this.force === undefined) {
            return;
        }
        delete this.force;
        this.from_string(rawhash);

        if (!this.serialized) {
            window.location.hash = this.options.deflocation;
            return;
        }
        if (!this.updatenext) {
            this.updatenext = true;
            return;
        }

        $.ajax({
            url: this.serialized,
            cache: false,
            dataType: 'json'
        }).done($.proxy(function(resp) {
            var callback = (resp.callback !== undefined) ? resp.callback : "default";

            this.callbacks[callback](resp);
            if (resp.respmsg) {
                $("body").notify("success", resp.respmsg, 2000);
            }
        }, this));
    }
};
