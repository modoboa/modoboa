(function($) {
    var objtable = null;

    function new_clickcb(evt) {
        var type = $("objects").get("name");
        var sizes = $("objects").get("rel").split(" ");

        evt.stop();
        SqueezeBox.open(this.rooturl + type + "/new/", {
            size: {x: parseInt(sizes[0]), y: parseInt(sizes[1])},
            handler: 'iframe'
        });
    };

    function remove_clickcb(evt) {
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
    };

    var methods = {
        init: function(rooturl, deloptions) {
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

            $$("a[name=new]").addEvent("click", new_clickcb);
            $$("a[name=remove]").addEvent("click", remove_clickcb);
        }
    };

    $.fn.Domains = function(method) {
        if (methods[method]) {
            return methods[method].apply(this, Array.prototype.slice.call(arguments, 1));
        } else if (typeof method === 'object' || !method) {
            return methods.init.apply(this, arguments);
        } else {
            $.error(gettext('Unknown method: ') + method);
        }
     };
})(jQuery);
