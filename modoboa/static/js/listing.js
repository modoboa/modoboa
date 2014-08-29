var Listing = function(options) {
    this.initialize(options);
};

Listing.prototype = {
    constructor: Listing,

    listing_defaults: {
        presp_container: '#pagination-responsive',
        pbar_container: '#bottom-bar-right',
        pbar_id: '#pagination_bar',
        sortable_selector: '.sortable',
        with_searchform: true
    },

    initialize: function(options) {
        this.options = $.extend({}, this.listing_defaults, options);
        this.tag_handlers = {};
        this.navobj = new History(this.options);
        $(document).on("click", this.options.pbar_container + " a",
            $.proxy(this.load_page, this));
        $(document).on("click", this.options.presp_container + " a",
            $.proxy(this.load_page, this));
        if (this.options.with_searchform) {
            this.init_searchform();
        }
    },

    /**
     * Initialize the search form.
     */
    init_searchform: function() {
        $("#searchquery").focus(function() {
            $(this).val("");
        }).blur($.proxy(function(e) {
            var $this = $(e.target);
            if ($this.val() === "") {
                if (this.navobj.getparam("searchquery")) {
                    $this.val(this.navobj.getparam("searchquery"));
                } else {
                    $this.val(gettext("Search"));
                }
            }
        }, this));
        if (this.navobj.getparam("searchquery") !== undefined) {
            $("#searchquery").val(this.navobj.getparam("searchquery"));
        }
        $("#searchform").submit($.proxy(this.do_search, this));
    },

    /**
     * Apply the current search pattern.
     */
    do_search: function(e) {
        e.preventDefault();
        var squery = $("#searchquery").val();
        if (squery !== "") {
            this.navobj.setparam("searchquery", squery);
        } else {
            this.navobj.delparam("searchquery");
        }
        this.navobj.update();
    },


    load_page: function(e) {
        var $link = get_target(e, "a");
        e.preventDefault();
        this.navobj.updateparams($link.attr("href")).update();
    },

    update_listing: function(data) {
        if (data.paginbar) {
            $(this.options.pbar_container).html(data.paginbar);
            $(this.options.presp_container).html(data.paginbar);
            $(this.options.pbar_id).find(".disabled a").click(function(e) {
                e.preventDefault();
            });
        }
        if (data.page && data.page != this.navobj.getparam("page")) {
            this.navobj.setparam("page", data.page).update(false, true);
        }
        var $sortables = $(this.options.sortable_selector);
        if ($sortables.length) {
            $(this.options.sortable_selector).sortable({
                onSortOrderChange: $.proxy(this.change_sort_order, this)
            });
            this.set_sort_order();
        }
    },

    set_sort_order: function() {
        var sort_order = this.navobj.getparam("sort_order");
        var sort_dir;

        if (!sort_order) {
            return;
        }
        if (sort_order[0] == '-') {
            sort_dir = "desc";
            sort_order = sort_order.substr(1);
        } else {
            sort_dir = 'asc';
        }
        $("th[data-sort_order=" + sort_order + "]").sortable('select', sort_dir);
    },

    change_sort_order: function(sort_order, dir) {
        if (dir == "desc") {
            sort_order = "-" + sort_order;
        }
        this.navobj.setparam("sort_order", sort_order).update();
    },

    register_tag_handler: function(name, handler) {
        this.tag_handlers[name] = handler;
        if (this.navobj.getparam(name + "filter") !== undefined) {
            var text = this.navobj.getparam(name + "filter");
            $("#taglist").append(this.make_tag(text, name));
        }
    },

    generic_tag_handler: function(tag, $link) {
        if (this.navobj.getparam(tag + "filter") === undefined && $link.hasClass(tag)) {
            var text = $link.attr("name");
            this.navobj.setparam(tag + "filter", text).update();
            $("#taglist").append(this.make_tag(text, tag));
            return true;
        }
        return false;
    },

    make_tag: function(text, type) {
        var $tag = $("<a />", {
            "name": type, "class" : "btn btn-default btn-xs",
            "html": text
        });
        
        $("<span />", {"class" : "glyphicon glyphicon-remove"}).prependTo($tag);
        $tag.click($.proxy(this.remove_tag, this));
        return $tag;
    },

    remove_tag: function(e) {
        var $tag = $(e.target);

        if ($tag.is("i")) {
            $tag = $tag.parent();
        }
        e.preventDefault();
        this.navobj.delparam($tag.attr("name") + "filter").update();
        $tag.remove();
    },

    filter_by_tag: function(e) {
        var $link = $(e.target);
        e.preventDefault();

        for (var name in this.tag_handlers) {
            if (this.tag_handlers[name].apply(this, [name, $link])) {
                break;
            }
        }
    }
};
