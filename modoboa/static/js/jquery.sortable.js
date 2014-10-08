(function($) {
    /**
     * Return an instance of Sortable.
     *
     * @constructor
     * @param {Object} element -
     * @param {Object} options - instance options
     */
     var Sortable = function(element, options) {
         this.initialize(element, options);
     };

     Sortable.prototype = {
         constructor: Sortable,

         initialize: function(element, options) {
             this.$element = $(element);
             this.options = $.extend({}, $.fn.sortable.defaults, options);
             this.$element.addClass('sort-header');
             this.listen();
         },

         listen: function() {
             this.$element.click($.proxy(this.sort, this));
         },

         change_sort_order: function(e, new_sort_order) {
             if (new_sort_order != this.$element.attr('data-sort_order')) {
                 this.$element.removeClass('sort-header-desc sort-header-asc');
             }
         },

         sort: function(e) {
             e.preventDefault();
             var dir = this.select();

             if (this.options.onSortOrderChange) {
                 this.options.onSortOrderChange(this.$element.attr('data-sort_order'), dir);
             }
         },

         /**
          * Mark a column as the one used to sort content.
          *
          * @this Sortable
          * @param {string} dir - optional sort direction (up or down)
          * @return {string} - new sort direction
          */
         select: function(dir) {
             $("span.sort-selection").remove();
             if (dir !== undefined) {
                 this.$element.removeClass("sort-header-" + ((dir == "asc") ? "desc" : "asc"));
                 this.$element.addClass("sort-header-" + dir);
             } else {
                 if (this.$element.hasClass("sort-header-desc")) {
                     this.$element
                         .removeClass("sort-header-desc")
                         .addClass("sort-header-asc");
                     dir = "asc";
                 } else {
                     this.$element
                         .removeClass("sort-header-asc")
                         .addClass("sort-header-desc");
                     dir = "desc";
                 }
             }
             this.$element.append($("<span/>", {
                 "class": "sort-selection fa fa-chevron-" + ((dir == 'asc') ? 'up' : 'down')
             }));
             return dir;
         }
     };

     $.fn.sortable = function(method) {
        var args = arguments;

        return this.each(function() {
            var $this = $(this),
                data = $this.data('sortable'),
                options = typeof method === "object" && method;

            if (!data) {
                $this.data('sortable', new Sortable(this, options));
                data = $this.data('sortable');
            }
            if (typeof method === "string") {
                data[method].apply(data, Array.prototype.slice.call(args, 1));
            }
        });
     };

     $.fn.sortable.defaults = {
         onSortOrderChange: null
     };
})(jQuery);
