var Domains = new Class({
    initialize: function(rooturl, deloptions) {
        this.rooturl = rooturl;
        if (deloptions != undefined) {
            this.deloptions = deloptions;
        } else {
            this.deloptions = new Array();
        }
        if ($("subcontent") != undefined) {
            SqueezeBox.assign($("subcontent").getElements('a[class=boxed]'), {
                parse: 'rel'
            });
        }
        setDivHeight("content", 20, 0);
        this.objtable = new HtmlTable($("objects_table"), {
            selectable: true
        });

        $$("a[name=new]").addEvent("click", this.new_clickcb.bind(this));
        $$("a[name=remove]").addEvent("click", this.remove_clickcb.bind(this));

    },

    new_clickcb: function(evt) {
        var type = $("objects").get("name");
        var sizes = $("objects").get("rel").split(" ");

        evt.stop();
        SqueezeBox.open(this.rooturl + type + "/new/", {
            size: {x: parseInt(sizes[0]), y: parseInt(sizes[1])},
            handler: 'iframe'
        });
    },

    remove_clickcb: function(evt) {
        evt.stop();
        if (this.objtable._selectedRows.length == 0) {
            return;
        }
        var type = $("objects").get("name");
        var selection = "";

        this.objtable._selectedRows.each(function(item) {
            var options = JSON.decode(item.get("rel"));

            if (options != undefined && options.ui_disabled != undefined &&
                options.ui_disabled == "True") {
                return;
            }
            if (selection != "") {
                selection += ",";
            }
            selection += item.get("id");
        });
        if (selection == "") {
            return;
        }
        new Confirmation(
            this.rooturl + type + "/delete/",
            "selection=" + selection,
            gettext('Remove this selection?'), {
                checkboxes: this.deloptions
            }
        );
    }
});
