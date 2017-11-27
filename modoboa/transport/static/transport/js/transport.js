/*
 * Transport javascript tools.
 */

function displayBackendSettings(name) {
    $('#backend_settings').find("div[class*=form-group]").hide();
    if (name !== '') {
        $('#backend_settings').find('[name*=' + name + '_]').each(function (index, input) {
            $(input).parents("div[class*=form-group]").show();
        });
    }
}

function transportFormCallback () {
    var $service_field = $('#id_service');

    $service_field.change(function (event) {
        displayBackendSettings($(this).val());
    });
    displayBackendSettings($service_field.val());

    $('.submit').one('click', $.proxy(function(e) {
        simple_ajax_form_post(e, {
            formid: 'transport_form',
            error_cb: transportFormCallback
        });
    }, this));
}

$(document).ready(function () {
    $('#searchquery').focus(function () {
        $(this).val('');
    }).blur(function (e) {
        var $this = $(this);
        if ($this.val() === '') {
            $this.val(gettext('Search'));
        }
    });
    $('a[name=deltransport]').confirm({
        question: function() { return this.$element.attr('title'); },
        method: 'DELETE'
    });
});
