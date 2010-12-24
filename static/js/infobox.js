var InfoBox = new Class({
    Implements: [Options, Events],
    options: {
        parent : null,
        message : "This is my info box!",
        width : 200
    },

    profiles: {
        gray : {"background" : "#EEEEEE", "border" : "#CCCCCC"},
        green : {"background" : "#DAF8DA", "border" : "#166D14"},
        red : {"background" : "#F9D2D2", "border" : "#FF2A00"},
        yellow : {"background" : "#FDE6B5", "border" : "#FF7F00"}
    },

    initialize: function(options) {
        this.setOptions(options);

        var boxleft = $(document.body).getSize().x / 2 - this.options.width / 2;
        this.box = new Element("div", {"id" : "infobox"});
        this.box.setStyles({
            "font-size" : "1em",
            "font-weight" : "bold",
            "text-align" : "left",
            "width" : this.options.width + "px",
            "padding" : "10px",
            "position" : "absolute",
            "top" : "0px",
            "left" : boxleft + "px",
            "display" : "none"
        });
        this.setProfile("gray");
        this.spinner = new Element("img", {
            "src" : "/static/css/spinner.gif"
        });
        this.spinner.setStyle("float", "left");
        this.spinner.inject(this.box);

        this.label = new Element("label").set("html", this.options.message);
        this.label.setStyles({
            "margin-left" : "10px"
        });
        this.label.inject(this.box);
        this.box.inject($(document.body));
    },

    setMessage: function(text) {
        this.label.set("html", text);
    },

    setProfile: function(color) {
        this.box.setStyles({
            "background" : this.profiles[color].background,
            "border" : "2px solid " + this.profiles[color].border
        });
    },

    info: function(message) {
        this.show(message, {
            profile: "green"
        });
    },

    error: function(message) {
        this.show(message, {
            profile: "red"
        });
    },

    warning: function(message) {
        this.show(message, {
            profile: "yellow"
        });
    },

    show: function(message, arguments) {
        if ($defined(this.start)) {
            if ($time() - this.start > this.delay) {
                $clear(this.showtimer);
                delete(this.start);
                delete(this.delay);
            } else {
                this.showtimer = this.show.delay(100, this, [message, arguments]);
                return;
            }
        }
        if ($defined(message)) {
            this.setMessage(message);
        }
        if ($defined(arguments.profile)) {
            this.setProfile(arguments.profile);
        }
        if ($defined(arguments.delay)) {
            this.start = $time();
            this.delay = arguments.delay * 1000;
        }
        if ($defined(arguments.spinner) && arguments.spinner) {
            this.spinner.setStyle("display", "block");
        } else {
            this.spinner.setStyle("display", "none");
        }
        this.box.setStyle("display", "block");
    },

    hide: function(timer) {
	this.timer = this.hide_cb.periodical(timer * 1000, this);
    },

    hide_cb: function() {
	$clear(this.timer);
        this.box.setStyle("display", "none");
    }
});
