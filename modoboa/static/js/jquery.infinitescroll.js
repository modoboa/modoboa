/**
 * Infinite scroll plugin for jQuery.
 *
 * @author {Antoine Nguyen}
 */
!function($) {
    'use strict';

    /**
     * Creates an instance of InfiniteScroll.
     *
     * @constructor
     * @this InfiniteScroll
     * @param {object} element
     * @param {dictionary} options - instance options
     */
    var InfiniteScroll = function(element, options) {
        this.$element = $(element);
        this.$data = $(element).data();
        this.$options = options;
        this.executing = false;
        this.end_of_results = false;
        if (this.$options.initial_pages !== undefined &&
            this.$options.initial_pages.length > 0) {
            this.current_page = this.$options.initial_pages[0];
            this.loaded_pages = this.$options.initial_pages;
        } else {
            this.current_page = 1;
            this.loaded_pages = [this.current_page];
        }
        this.resume();
    };

    InfiniteScroll.prototype = {
        constructor: InfiniteScroll,

        /**
         * Scroll event handler.
         *
         * @this InfiniteScroll
         */
        on_scroll: function() {
            var bottom = this.$options.calculate_bottom(this.$element);

            if (bottom === undefined || bottom < 0) {
                return;
            }
            if (this.$element.scrollTop() >= bottom) {
                this.load_next_page();
            } else if (this.$element.scrollTop() === 0) {
                this.load_previous_page();
            }
        },

        /**
         * Load the previous page from the server.
         *
         * @private
         * @this InfiniteScroll
         */
        load_previous_page: function() {
            var $this = this;

            if ($this.executing || $.inArray(1, $this.loaded_pages) != -1) {
                return;
            }

            while ($this.current_page > 0) {
                $this.current_page -= 1;
                if ($.inArray($this.current_page, $this.loaded_pages) == -1) {
                    break;
                }
            }
            if ($this.current_page === 0) {
                $this.current_page = 1;
                return;
            }
            this.load_page("up");
        },

        /**
         * Load the next page from the server.
         *
         * @this InfiniteScroll
         */
        load_next_page: function() {
            var $this = this;

            if ($this.executing || $this.end_of_results) {
                return;
            }
            while (true) {
                $this.current_page += 1;
                if ($.inArray($this.current_page, $this.loaded_pages) == -1) {
                    break;
                }
            }
            this.load_page("down");
        },

        /**
         * Load a page's content.
         *
         * @private
         * @this InfiniteScroll
         * @param {string} direction - direction of the scroll (up or down)
         */
        load_page: function(direction) {
            var args = (this.$options.get_args) ? this.$options.get_args() : {};
            var $this = this;

            this.executing = true;
            args.page = this.current_page;
            $.ajax({
                contentType: 'application/json; charset=UTF-8',
                data: args,
                url: $this.$options.url,
                type: 'GET',
                success: function(data) {
                    $this.$options.process_results(data, direction);
                    if (data.length === 0) {
                        $this.end_of_results = true;
                        $this.$options.end_of_list_reached($this.$element);
                    }
                    $this.executing = false;
                    $this.loaded_pages.push($this.current_page);
                }
            });
        },

        /**
         * Reset the loaded pages cache.
         *
         * @this InfiniteScroll
         * @param {Array} new_pages - the new loaded pages
         */
        reset_loaded_pages: function(new_pages) {
            if (new_pages !== undefined) {
                this.current_page = new_pages[0];
                this.loaded_pages = new_pages;
            } else {
                this.current_page = this.$options.initial_page;
                this.loaded_pages = [this.$options.initial_pages];
            }
            this.end_of_results = false;
        },

        /**
         * Suspend the "infinite scroll" mode.
         *
         * @this InfiniteScroll
         */
        pause: function() {
            this.$element.unbind("scroll");
        },

        /**
         * Resume the "infinite scroll" mode.
         *
         * @this InfiniteScroll
         */
        resume: function() {
            this.$element.scroll($.proxy(this.on_scroll, this));
        }
    };

    $.fn.infinite_scroll = function (option) {
        var args = arguments;

        return this.each(function () {
            var $this = $(this),
                data = $this.data('infinite-scroll'),
                options = $.extend(
                    {}, $.fn.infinite_scroll.defaults,
                    typeof option == 'object' && option
                );

                if (!data) {
                    $this.data('infinite-scroll', (
                        data = new InfiniteScroll(this, options))
                    );
                }
                if (typeof option == 'string') {
                    data[option].apply(data, Array.prototype.slice.call(args, 1));
                }
        });
    };

    $.fn.infinite_scroll.defaults = {
        initial_page: 1,
        calculate_bottom: null,
        get_data: null,
        process_results: null,
        end_of_list_reached: null,
        url: ''
    };

    $.fn.infinite_scroll.Constructor = InfiniteScroll;
}(window.jQuery);
