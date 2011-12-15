
var DynamicTextInput = new Class({
    Implements: [Options],

    options: {
        parentContainer: null,
        containerLevel: 1
    },

    initialize: function(targets, options) {
        if (!$defined(targets) || !targets.length) {
            return;
        }
        this.fields_cnt = 0;
        for (var cpt = 0; cpt < targets.length; cpt++) {
            var target = targets[cpt];
            var btn;

            if (cpt == 0) {
                btn = new Element("img", {
                    src: parent.static_url("pics/add.png")
                });
                btn.addEvent("click", this.newelement.bind(this));
            } else {
                var btnid = "btn_" + cpt;
                btn = new Element("img", {
                    src: parent.static_url("pics/remove.png"),
                    id: btnid
                });
                btn.addEvent("click", this.removeelement.bind(this));
            }
            btn.setStyles({
                "float": "right",
                "margin-top": "2px"
            });
            btn.inject(target, "after");
            this.fields_cnt++;
        }
        this.nextid = targets.length;
        this.target = targets[0];
        this.setOptions(options);
    },

    createfield: function() {
        var div = new Element("div").addClass("row");
        var label = new Element("label").inject(div);
        var ninput = new Element("input", {
            type: "text",
            id: this.target.get("id") + "_" + this.nextid,
            name: this.target.get("name"),
            value: this.target.get("value")
        }).inject(div);

        return [div, ninput];
    },

    newelement: function(event) {
        if (this.target.get("value") == "") {
            return;
        }
        var field = this.createfield();
        var delbtn = new Element("img", {
            id: "delbtn_" + this.nextid,
            src: parent.static_url("pics/remove.png")
        });
        this.nextid += 1;
        delbtn.setStyles({
            "float" : "right",
            "margin-top": "2px"
        });
        if (!this.options.parentContainer) {
            var container = this.target;
            for (var i = 0; i < this.options.containerLevel; i++) {
                container = container.getParent()
            }
            field[0].inject(container, "after");
        } else {
            field[0].inject(this.options.parentContainer);
        }
        delbtn.inject(field[1], "after");
        delbtn.addEvent("click", this.removeelement.bind(this));
        this.target.set("value", "");
        this.fields_cnt++;
    },

    removeelement: function(event) {
        var id = (event.target.get("id").split("_"))[1];
        var input = $("id_" + this.target.get("name") + "_" + id);

        input.destroy();
        event.target.destroy();
        this.fields_cnt--;
    }
});