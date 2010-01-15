window.addEvent('domready', function() {
    SqueezeBox.assign($$('a.boxed'), {
        parse: 'rel'
    });
    
    new DatePicker("#untildate", {
        pickerClass: "datepicker_vista",
        allowEmpty: true
    });
});
