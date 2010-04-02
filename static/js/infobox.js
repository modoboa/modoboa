var InfoBox = new Class({
    Implements: [Options, Events],
    options: {
        parent : null,
        message : "This is my info box!",
        width : 200,
    },

    profiles: {
        gray : {"background" : "#EEEEEE", "border" : "#CCCCCC"},
        green : {"background" : "#DAF8DA", "border" : "#166D14"},
        red : {"background" : "#F9D2D2", "border" : "#FF2A00"},
        yellow : {"background" : "#FDE6B5", "border" : "#FF7F00"}
    },

    initialize: function(options) {
        this.setOptions(options);

        var boxleft = document.body.getSize().x / 2 - this.options.width / 2;
        this.box = new Element("div", {"id" : "infobox"});
        this.box.setStyles({
            "font-size" : "normal",
            "font-weight" : "bold",
            "text-align" : "left",
            "width" : this.options. width + "px",
            "padding" : "10px",
            "position" : "absolute",
            "top" : "0px",
            "left" : boxleft + "px",
            "display" : "none"
        });
        this.setProfile("gray");
        this.spinner = new Element("img", {
            "src" : "/static/stylesheets/spinner.gif"
        });
        this.spinner.setStyle("float", "left");
        this.spinner.inject(this.box);

        this.label = new Element("label").set("html", this.options.message);
        this.label.setStyles({
            "margin-left" : "10px"
        });
        this.label.inject(this.box);
        this.box.inject(document.body);
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

    notice: function(message) {
        this.setProfile("green");
        this.setMessage(message);
    },

    error: function(message) {
        this.setProfile("red");
        this.setMessage(message);
    },

    warning: function(message) {
        this.setProfile("yellow");
        this.setMessage(message);
    },

    show: function(message, prof, delay) {
        if ($defined(this.start)) {
            if ($time() - this.start > this.delay) {
                $clear(this.showtimer);
                delete(this.start);
                delete(this.delay);
            } else {
                this.showtimer = this.show.delay(100, this, [message, prof]);
                return;
            }
        }
        if ($defined(message)) {
            this.setMessage(message);
        }
        if ($defined(prof)) {
            this.setProfile(prof);
        }
        if ($defined(delay)) {
            this.start = $time();
            this.delay = delay * 1000;
        }
        this.box.setStyle("display", "block");
    },
    
    hide: function(timer) {
        if ($defined(timer)) {
            this.timer = this.hide.periodical(timer * 1000, this);
            return;
        }
        $clear(this.timer);
        this.box.setStyle("display", "none");
    },
});