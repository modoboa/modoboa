(function($) {
    var DynamicCondition = function(element, options) {
        this.$element = $(element);
        this.options = $.extend({}, $.fn.dyncondition.defaults, options);
        this.fields_cnt = 1;
        this.nextid = 1;

        var $addlink = $('<a />', {
            href: '#',
            id: this.$element.attr("id") + '_rmbtn',
            html: '<i class="fa fa-plus"></i>'
        });
        $("select[name*=cond_target_]").change($.proxy(this.target_change, this));
        $addlink.click($.proxy(this.addfields, this));
        this.$element.append($addlink);

        for (var cpt = 1; true; cpt++) {
            var $div = $("#condition_" + cpt);

            if (!$div.length) {
                break;
            }
            $div.append(this.newrmlink());
            this.nextid++;
            this.fields_cnt++;
        }
    };

    DynamicCondition.prototype = {
        constructor: DynamicCondition,

        loadoperators: function($container, tpl) {
            $container.empty();
            for (var ocpt = 0; ocpt < tpl.operators.length; ocpt++) {
                var $opt = $("<option />", {
                    value: tpl["operators"][ocpt][0],
                    html: tpl["operators"][ocpt][1]
                });

                $container.append($opt);
            }
        },

        removefields: function(e) {
            var $link = $(e.target).parent();
            var id = $link.attr("id");

            e.preventDefault();
            $("#" + id.replace("_rmbtn", "")).remove();
            this.fields_cnt--;
        },

        newrmlink: function() {
            return $('<a />', {
                href: '#',
                id: 'condition_' + this.nextid + '_rmbtn',
                html: '<i class="fa fa-trash"></i>'
            }).click($.proxy(this.removefields, this));
        },

        addfields: function(e) {
            e.preventDefault();
            var $div = $("<div />", {
                id: "condition_" + this.nextid, 'class': "item"
            });
            var $condtarget = $("<select />", {
                id: "id_cond_target_" + this.nextid,
                name: "cond_target_" + this.nextid,
                class: "form-control element-inline-block"
            }).change($.proxy(this.target_change, this));
            var $condoperator = $("<select />", {
                id: "id_cond_operator_" + this.nextid,
                name: "cond_operator_" + this.nextid,
                class: "form-control element-inline-block"
            });
            var $condvalue = $("<input />", {
                id: "id_cond_value_" + this.nextid,
                name: "cond_value_" + this.nextid,
                type: "text",
                class: "form-control element-inline-block"
            });
            var $rmlink = this.newrmlink();

            for (var cpt = 0; cpt < this.options.templates.length; cpt++) {
                var tpl = this.options.templates[cpt];
                var $opt = $("<option />", {
                    value: tpl.name,
                    html: tpl.label
                });

                $condtarget.append($opt);
                if (tpl.name != this.options.defaultcond) {
                    continue;
                }
                this.loadoperators($condoperator, tpl);
            }

            $div.append($condtarget, $condoperator, $condvalue, $rmlink);
            $condtarget.wrap('<div class="col-lg-3 col-md-3 col-sm-3"/>');
            $condoperator.wrap('<div class="col-lg-3 col-md-3 col-sm-3"/>');
            $condvalue.wrap('<div class="col-lg-4 col-md-4 col-sm-4"/>');
            this.$element.after($div);
            this.nextid++;
            this.fields_cnt++;
        },

        target_change: function(e) {
            var $target = $(e.target);
            var parts = $target.attr("name").split("_");
            var $container = $("#id_cond_operator_" + parts[2]);

            for (var cpt = 0; cpt < this.options.templates.length; cpt++) {
                var tpl = this.options.templates[cpt];

                if (tpl.name != $target.val()) {
                    continue;
                }
                this.loadoperators($container, tpl);
                break;
            }
        },

        counter: function() {
            return this.fields_cnt;
        }
    };

    $.fn.dyncondition = function(method) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('dyncondition'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('dyncondition', new DynamicCondition(this, options));
            }
            if (typeof method === "string") {
                data[method]();
            }
        });
    };

    $.fn.dyncondition.defaults = {
        defaultcond: "Subject",
        templates: []
    };

})(jQuery);

/*
 * Dynamic actions class
 */
(function($) {
    var DynamicAction = function(element, options) {
        this.$element = $(element);
        this.options = $.extend({}, $.fn.dynaction.defaults, options);
        this.nextid = 1;
        this.fields_cnt = 1;

        var $addlink = $('<a />', {
            href: '#',
            id: this.$element.attr("id") + '_rmbtn',
            html: '<i class="fa fa-plus"></i>'
        });
        $("select[name*=action_name_]").change($.proxy(this.name_change, this));
        $addlink.click($.proxy(this.addfields, this));
        this.$element.append($addlink);

        for (var cpt = 1; true; cpt++) {
            var $div = $("#action_" + cpt);

            if (!$div.length) {
                break;
            }
            $div.append(this.newrmlink());
            this.nextid++;
            this.fields_cnt++;
        }

        $("#id_action_arg_0_0").find("option").each(function() {
            var $this = $(this),
                cpt = 1,
                start = 0,
                value = $this.val();

            while (true) {
                var id = value.indexOf(options.hdelimiter, start);
                if (id == -1) {
                    break;
                }
                $this.css("margin-left", (cpt * 20) + "px");
                cpt++;
                start = id + 1;
            }
        });

        this.$fdoptions = $("#id_action_arg_0_0").find("option");
    };

    DynamicAction.prototype = {
        constructor: DynamicAction,

        loadargs: function(id, tpl) {
            var res = [];

            for (var acpt = 0; acpt < tpl.args.length; acpt++) {
                var argname = "action_arg_" + id + "_" + acpt;
                var $child = null;

                if (tpl.args[acpt].type == "list") {
                    $child = $("<select />", {id: "id_" + argname, name: argname, class: "form-control"});
                    if (tpl.args[acpt].vloader != undefined) {
                        this[tpl.args[acpt].vloader]($child);
                    }
                } else if (tpl.args[acpt].type == "string") {
                    $child = $("<input />", {
                        type: "text",
                        id: "id_" + argname,
                        name: argname,
                        class: "form-control"
                    });
                }
                res.push($child);
            }
            return res;
        },

        deletePrevArgs: function(id) {
            for (var cpt = 0; true; cpt++) {
                var $arg = $("#id_action_arg_" + id + "_" + cpt);
                if (!$arg.length) {
                    break;
                }
                $arg.remove();
            }
        },

        name_change: function(e) {
            var $target = $(e.target);
            var parts = $target.attr("name").split("_");
            var $pos = $("#action_" + parts[2] + "_rmbtn");

            e.preventDefault();
            this.deletePrevArgs(parts[2]);
            for (var cpt = 0; cpt < this.options.templates.length; cpt++) {
                var tpl = this.options.templates[cpt];
                if (tpl.name != $target.val()) {
                    continue;
                }
                $.each(this.loadargs(parts[2], tpl), function(idx, arg) {
                    $pos.before(arg);
                });
            }
        },

        newrmlink: function() {
            return $('<a />', {
                href: '#',
                id: 'action_' + this.nextid + '_rmbtn',
                html: '<i class="fa fa-trash"></i>'
            }).click($.proxy(this.removefields, this));
        },

        addfields: function(e) {
            e.preventDefault();
            var $div = $("<div />", {id: "action_" + this.nextid, "class": "item"});
            var $actioname = $("<select />", {
                id: "id_action_name_" + this.nextid,
                name: "action_name_" + this.nextid,
                class: "form-control element-inline-block"
            });
            var $rmlink = this.newrmlink();
            var args = null;

            for (var cpt = 0; cpt < this.options.templates.length; cpt++) {
                var tpl = this.options.templates[cpt];
                var $opt = $("<option />", {
                    value: tpl.name,
                    html: tpl.label
                });

                $actioname.append($opt);
                if (tpl.name != this.options.defaultaction) {
                    continue;
                }
                args = this.loadargs(this.nextid, tpl);
            }
            $div.append($actioname);
            $actioname.change($.proxy(this.name_change, this));
            $.each(args, function(idx, element) {
                $div.append(element);
                element.wrap('<div class="col-lg-5 col-md-5 col-sm-5"/>');
            });

            $actioname.wrap('<div class="col-lg-5 col-md-5 col-sm-5"/>');
            $div.append($rmlink);
            this.$element.after($div);
            this.nextid++;
            this.fields_cnt++;
        },

        removefields: function(e) {
            var $link = $(e.target).parent();
            var id = $link.attr("id");

            e.preventDefault();
            $("#" + id.replace("_rmbtn", "")).remove();
            this.fields_cnt--;
        },

        userfolders: function($container) {
            this.$fdoptions.each(function() {
                $container.append($(this).clone());
            });
        }

    };

    $.fn.dynaction = function(method) {
        return this.each(function() {
            var $this = $(this),
                data = $this.data('dynaction'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('dynaction', new DynamicAction(this, options));
            }
            if (typeof method === "string") {
                data[method]();
            }
        });
    };

    $.fn.dynaction.defaults = {
        defaultaction: "fileinto",
        hdelimiter: '.',
        templates: []
    };
})(jQuery);