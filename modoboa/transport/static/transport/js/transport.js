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
}

$(document).ready(function () {
    $(this).bind('domwizard_init', transportFormCallback);
    $(this).bind('domform_init', transportFormCallback);
});
