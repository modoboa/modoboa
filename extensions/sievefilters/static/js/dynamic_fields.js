
var DynamicCondition = new Class({

    Extends: DynamicTextInput,

    options: {
        defaultcond: "Subject",
        templates: []
    },

    loadoperators: function(container, tpl) {
        container.empty();
        for (var ocpt = 0; ocpt < tpl["operators"].length; ocpt++) {
            var opt = new Element("option", {
                value: tpl["operators"][ocpt][0],
                html: tpl["operators"][ocpt][1]
            });
            opt.inject(container);
        }
    },

    onTargetChange: function(event) {
        var parts = event.target.get("name").split("_");
        var container = $("id_cond_operator_" + parts[2]);

        for (var cpt = 0; cpt < this.options.templates.length; cpt++) {
            var tpl = this.options.templates[cpt];
            if (tpl["name"] != event.target.get("value")) {
                continue;
            }
            this.loadoperators(container, tpl);
            break;
        }
    },

    createfield: function() {
        var div = new Element("div", {"class": "item"});
        var condtarget = new Element("select", {
            id: "id_cond_target_" + this.nextid,
            name: "cond_target_" + this.nextid
        });
        var condoperator = new Element("select", {
            id: "id_cond_operator_" + this.nextid,
            name: "cond_operator_" + this.nextid
        });
        var condvalue = new Element("input", {
            id: "id_cond_value_" + this.nextid,
            name: "cond_value_" + this.nextid,
            type: "text"
        });

        for (var cpt = 0; cpt < this.options.templates.length; cpt++) {
            var tpl = this.options.templates[cpt];
            var opt = new Element("option", {
                value: tpl["name"],
                html: tpl["label"]
            });
            opt.inject(condtarget);

            if (tpl["name"] != this.options.defaultcond) {
                 continue;
            }
            this.loadoperators(condoperator, tpl);
        }
        condtarget.inject(div);
        condtarget.addEvent("change", this.onTargetChange.bind(this));
        condoperator.inject(div);
        condvalue.inject(div);
        return [div, condvalue];
    },

    removeelement: function(event) {
        var id = (event.target.get("id").split("_"))[1];

        event.stop();
        $("id_cond_target_" + id).destroy();
        $("id_cond_operator_" + id).destroy();
        $("id_cond_value_" + id).destroy();
        event.target.destroy();
        this.fields_cnt--;
    }
});

var DynamicAction = new Class({
    Extends: DynamicTextInput,

    options: {
        defaultaction: "fileinto",
        templates: [],
        ufolders_url: null
    },

    initialize: function(targets, options) {
        this.parent(targets, options);
        $("id_action_arg_0_0").getElements("option").each(function(item) {
            var cpt = 1;
            var start = 0;
            var value = item.get("value");

            while (true) {
                var id = value.indexOf(".", start);
                if (id == -1) {
                    break;
                }
                item.setStyle("margin-left", (cpt * 20) + "px");
                cpt++;
                start = id + 1;
            }
        });
        this.fdoptions = $("id_action_arg_0_0").getElements("option");
    },

    loadargs: function(id, tpl) {
        var res = new Elements();

        for (var acpt = 0; acpt < tpl["args"].length; acpt++) {
            var argname = "action_arg_" + id + "_" + acpt;
            var child = null;

            if (tpl["args"][acpt]["type"] == "list") {
                child = new Element("select", {id: "id_" + argname, name: argname});
                if ($defined(tpl["args"][acpt]["vloader"])) {
                    this[tpl["args"][acpt]["vloader"]](child);
                }
            } else if (tpl["args"][acpt]["type"] == "string") {
                child = new Element("input", {type: "text",
                                              id: "id_" + argname, name: argname});
            }
            res.push(child);
        }
        return res;
    },

    deletePrevArgs: function(id) {
        for (var cpt = 0; true; cpt++) {
            var arg = $("id_action_arg_" + id + "_" + cpt);
            if (!$defined(arg)) {
                break;
            }
            arg.destroy();
        }
    },

    onNameChange: function(event) {
        var parts = event.target.get("name").split("_");
        var container = event.target.getParent();

        event.stop();
        this.deletePrevArgs(parts[2]);
        for (var cpt = 0; cpt < this.options.templates.length; cpt++) {
            var tpl = this.options.templates[cpt];
            if (tpl["name"] != event.target.get("value")) {
                continue;
            }
            var args = this.loadargs(parts[2], tpl);
            args.inject(container);
        }
    },

    createfield: function() {
        var div = new Element("div", {"class": "item"});
        var actionname = new Element("select", {
            id: "id_action_name_" + this.nextid,
            name: "action_name_" + this.nextid
        });
        var args = null;

        for (var cpt = 0; cpt < this.options.templates.length; cpt++) {
            var tpl = this.options.templates[cpt];
            var opt = new Element("option", {
                value: tpl["name"],
                html: tpl["label"]
            });
            opt.inject(actionname);

            if (tpl["name"] != this.options.defaultaction) {
                 continue;
            }
            args = this.loadargs(this.nextid, tpl);
        }
        actionname.inject(div);
        actionname.addEvent("change", this.onNameChange.bind(this));
        args.inject(div);
        return [div, actionname];
    },

    removeelement: function(event) {
        var id = (event.target.get("id").split("_"))[1];

        event.stop();
        $("id_action_name_" + id).destroy();
        for (var cpt = 0; true; cpt++) {
            var arg = $("id_action_arg_" + id + "_" + cpt);
            if (!$defined(arg)) {
                break;
            }
            arg.destroy();
        }
        event.target.destroy();
        this.fields_cnt--;
    },

    userfolders: function(container) {
        this.fdoptions.each(function(item) {
            item.clone().inject(container);
        });
    }
});