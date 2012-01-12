var Resellers = new Class({
    initialize: function() {
        this.resellers_table = new HtmlTable($("resellers_table"), {
            selectable: true
        });
        SqueezeBox.assign($("content").getElements('a[class=boxed]'), {
            parse: 'rel'
        });

        $$("a[name=remove]").addEvent("click", this.remove_clickcb.bind(this));
    },

    remove_clickcb: function(evt) {
        evt.stop();
        if (this.resellers_table._selectedRows.length == 0) {
            return;
        }

        if (!confirm(gettext("Remove this selection?"))) {
            return;
        }

        var selection = "";

        this.resellers_table._selectedRows.each(function(item) {
            if (selection != "") {
                selection += ",";
            }
            selection += item.get("id");
        });

        new Request.JSON.mdb({
            url: evt.target.get("href"),
            method: "GET",
            onSuccess: function(res) {
                if (res.status == "ok") {
		    window.location.reload();
		}
            }
        }).send("selection=" + selection);
    }
});