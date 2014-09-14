/**
 * Infinite scroll plugin for jQuery.
 *
 */
!function($) {
    'use strict';

    var InfiniteScroll = function(element, options) {
        this.$element = $(element);
        this.$data = $(element).data();
        this.$options = options;
        this.executing = false;
        this.end_of_results = false;
        this.current_page = 1;
        var that = this;

        this.$element.scroll(function() {
            if (that.$element.scrollTop() >= that.$options.calculate_bottom(that.$element)) {
                that.load_more();
            }
        });
    };

    InfiniteScroll.prototype = {
        constructor: InfiniteScroll,

        load_more: function() {
            var $this = this;

            if ($this.executing || $this.end_of_results) {
                return;
            }
            /*$this.$element.find('.spinner').removeClass('hide');*/
            $this.executing = true;
            $this.current_page += 1;
            var args = $this.$options.get_args();
            args.page = $this.current_page;
            $.ajax({
                contentType: 'application/json; charset=UTF-8',
                data: args,
                url: $this.$options.url,
                type: 'GET',
                success: function(data) {
                    $this.$options.process_results(data);
                    if (data.length === 0) {
                        $this.end_of_results = true;
                        /*$this.$element.find('#end-of-results').removeClass('hide');*/
                    }
                    //$this.$element.find('.spinner').addClass('hide');
                    $this.executing = false;
                }
            });
        }
    };

    $.fn.infinite_scroll = function (option) {
        return this.each(function () {
            var $this = $(this),
                data = $this.data('infinite-scroll'),
                options = $.extend({}, $.fn.infinite_scroll.defaults, typeof option == 'object' && option);

                if (!data) {
                    $this.data('infinite-scroll', (data = new InfiniteScroll(this, options)));
                }
                if (typeof options == 'string') {
                    data[options]();
                }
        });
    };

    $.fn.infinite_scroll.defaults = {
        calculate_bottom: null,
        get_data: null,
        process_results: null,
        url: ''
    };

    $.fn.infinite_scroll.Constructor = InfiniteScroll;
}(window.jQuery);
