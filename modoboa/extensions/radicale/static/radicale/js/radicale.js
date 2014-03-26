var Radicale = function() {

};

Radicale.prototype = {
    constructor: Radicale,

    initialize: function() {

    },

    add_calendar_cb: function() {
        $("#wizard").cwizard({
            formid: "newcal_form"
        });
    }
};
