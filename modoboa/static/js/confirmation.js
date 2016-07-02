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
             this.box.on('hidden.bs.modal', $.proxy(this.hidden_callback, this));
         },

         buildcheckboxes: function() {
             var result = "";

             if (!this.options.checkboxes || !Object.keys(this.options.checkboxes).length) {
                 return "";
             }
             result = '<form class="form-horizontal">';
             $.each(this.options.checkboxes, function(key, val) {
                 result += "<div class='form-group'><div class='col-xs-12'><div class='checkbox'><label><input type='checkbox' name='{0}' value='' />{1}</label></div></div></div>".format(key, val);
             });
             result += '</form>';
             return result;
         },

         buildbox: function() {
             var box = $('<div />', {
                 id: "confirmbox",
                 'class': "modal fade"
             });
             var question = (typeof this.options.question === 'function') ?
                 this.options.question.apply(this) : this.options.question;
             var checkboxes = this.buildcheckboxes();
             var body = "";

             if (this.options.warning) {
                   body += '<div class="alert alert-danger"><h4>{0}</h4>{1}</div>'.format(gettext("Warning"), this.options.warning);
             }
             if (checkboxes !== "") {
                 body += "<p>{0}</p>".format(checkboxes);
             }

             var content = '<div class="modal-dialog"><div class="modal-content">';
             var title_patten = '<div class="{0}"><h3 class="modal-title">{1}</h3></div>';

             if (body !== "") {
                 content += title_patten.format("modal-header", question);
                 content += '<div class="modal-body">{0}</div>'.format(body);
             } else {
                 content += title_patten.format("modal-body", question);
             }
             content += '<div class="modal-footer"><a href="#" class="btn btn-primary">Ok</a><a href="#" class="btn btn-default">{0}</a></div>'.format(gettext("Cancel"));

             box.append($(content));

             box.find(".btn-primary").click(function(evt) {
                 evt.preventDefault();
                 box.data('result', true);
                 box.modal('hide');
             });

             box.find(".btn-default").click(function(evt) {
                 evt.preventDefault();
                 box.modal('hide');
             });

             return box;
         },

         hidden_callback: function() {
             if (this.box.data('result') === undefined) {
                 return;
             }
             var params = "";

             $('input[type=checkbox]:checked').each(function() {
                 if (params !== "") {
                     params += "&";
                 }
                 params += $(this).attr("name") + "=true";
             });
             $.ajax({
                 cache: false,
                 type: this.options.method,
                 data: params,
                 url: this.$element.attr('href')
             }).done($.proxy(function(data) {
                 if (this.options.success_cb !== undefined) {
                     this.options.success_cb(data);
                     return;
                 }
                 window.location.reload();
             }, this));
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
