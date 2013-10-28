(function($) {
     var Confirm = function(element, options) {
         this.$element = $(element);
         this.options = $.extend({}, $.fn.confirm.defaults, options);
         this.$element.click($.proxy(this.show, this));
     };

     Confirm.prototype = {
         constructor: Confirm,

         show: function(e) {
             e.preventDefault();

             this.box = this.buildbox();
             this.box.modal();
             this.box.on('hidden', $.proxy(this.hidden_callback, this));
         },

         buildcheckboxes: function() {
             var result = "";

             if (!this.options.checkboxes) {
                 return "";
             }
             result = '<form class="form-inline">';
             $.each(this.options.checkboxes, function(key, val) {
                 result += "<label class='checkbox'><input type='checkbox' name='" + key + "' value='' />";
	             result += val + "</label>";
             });
             result += '</form>';
             return result;
         },

         buildbox: function() {
             var box = $('<div />', {
                 id: "confirmbox",
                 'class': "modal"
             });
             var question = (typeof this.options.question == 'function')
                 ? this.options.question.apply(this) : this.options.question;

             box.append($('<div class="modal-body">'
                 + '<h4>' + question + '</h4>'));
             var $container = $("<div />", {"class" : "container-fluid"});
             box.append($container);
             if (this.options.warning) {
                 $container.append($("<div />", {"class" : "row-fluid"})
                     .append($("<div />", {
                         "class": "alert alert-danger",
                         html: "<h4>" + gettext("Warning") + "</h4>" + this.options.warning
                     }))
                 );
             }

             $container.append('<p>' + this.buildcheckboxes() + '</p>');
             box.append("</div>");

             var footer = $('<div class="modal-footer" />');
             var cancel_btn = $('<a href="#" class="btn">' + gettext("Cancel") + "</a>");
             var ok_btn = $('<a href="#" class="btn btn-primary">Ok</a>');

             ok_btn.click(function(evt) {
                 evt.preventDefault();
                 box.data('result', true);
                 box.modal('hide');
             });

             cancel_btn.click(function(evt) {
                 evt.preventDefault();
                 box.modal('hide');
             });

             footer.append(ok_btn, cancel_btn);
             box.append(footer);
             return box;
         },

         hidden_callback: function() {
             if (this.box.data('result') == undefined) {
                 return;
             }
             var params = "";

             $('input[type=checkbox]:checked').each(function() {
                 if (params != "") {
                     params += "&";
                 }
                 params += $(this).attr("name") + "=true";
             });
             $.ajax({
                 cache: false,
                 method: this.options.method,
                 data: params,
                 url: this.$element.attr('href')
             }).done($.proxy(function(data) {
                 if (this.options.success_cb != undefined) {
                     this.options.success_cb(data);
                     return;
                 }
                 window.location.reload();
             }, this)).fail(function(jqxhr) {
                 var data;
                 try {
                     data = $.parseJSON(jqxhr.responseText);
                 } catch (e) {
                     data = gettext('Internal Error');
                 }
                 $("body").notify("error", data);
             });
             this.box.remove();
         }
     };

     $.fn.confirm = function(method) {
         return this.each(function() {
             var $this = $(this),
                 data = $this.data('confirm'),
                 options = typeof method === "object" && method;

             if (!data) {
                 $this.data('confirm', new Confirm(this, options));
             }
             if (typeof method === "string") {
                 data[method]();
             }
         });
     };

     $.fn.confirm.defaults = {
         question: "",
         method: "GET",
         warning: null,
         checkboxes: null
     };

})(jQuery);
