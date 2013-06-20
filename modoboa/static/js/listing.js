var Listing = function(options) {
    this.initialize(options);
};

Listing.prototype = {
    constructor: Listing,

    listing_defaults: {
        pbar_container: '#bottom-bar-right',
        pbar_id: '#pagination_bar',
        sortable_selector: '.sortable'
    },

    initialize: function(options) {
        this.options = $.extend({}, this.listing_defaults, options);
        $(document).on("click", this.options.pbar_container + " a",
            $.proxy(this.load_page, this));
    },

    load_page: function(e) {
        var $link = get_target(e, "a");
        e.preventDefault();
        this.navobj.updateparams($link.attr("href")).update();
    },

    update_listing: function(data) {
        if (data.paginbar) {
            $(this.options.pbar_container).html(data.paginbar);
            $(this.options.pbar_id).find(".disabled a").click(function(e) {
                e.preventDefault();
            });
        }
        if (data.page != this.navobj.getparam("page")) {
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
    }
};