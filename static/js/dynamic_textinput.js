
var DynamicTextInput = new Class({
    Implements: [Options],

    options: {

    },

    initialize: function(targets, options) {
        if (!$defined(targets) || !targets.length) {
            return;
        }
        for (var cpt = 0; cpt < targets.length; cpt++) {
            var target = targets[cpt];
            var btn;

            if (cpt == 0) {
                btn = new Element("img", {
                    src: parent.static_url("pics/add.png")
                });
                btn.addEvent("click", this.newinput.bind(this));
            } else {
                var btnid = "btn_" + cpt;
                btn = new Element("img", {
                    src: parent.static_url("pics/remove.png"),
                    id: btnid
                });
                btn.addEvent("click", this.removeinput.bind(this));
            }
            btn.setStyles({
                "float": "right",
                "margin-top": "2px"
            });
            btn.inject(target, "after");
        }
        this.nextid = targets.length;
        this.target = targets[0];
        this.setOptions(options);
    },

    newinput: function(event) {
        if (this.target.get("value") == "") {
            return;
        }
        var coords = this.target.getCoordinates();
        var div = new Element("div").addClass("row");
        var label = new Element("label").inject(div);
        var ninput = new Element("input", {
            type: "text",
            id: this.target.get("id") + "_" + this.nextid,
            name: this.target.get("name"),
            value: this.target.get("value")
        }).inject(div);
        var delbtn = new Element("img", {
            id: "delbtn_" + this.nextid,
            src: parent.static_url("pics/remove.png")
        });

        this.nextid += 1;
        delbtn.setStyles({
            "float" : "right",
            "margin-top": "2px"
        });
        div.inject(this.target.getParent(), "after");
        delbtn.inject(ninput, "after");
        delbtn.addEvent("click", this.removeinput.bind(this));
        this.target.set("value", "");
    },

    removeinput: function(event) {
        var id = (event.target.get("id").split("_"))[1];
        var input = $("id_" + this.target.get("name") + "_" + id);

        input.destroy();
        event.target.destroy();
    }
});