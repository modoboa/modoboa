# coding: utf-8

from modoboa.lib import parameters, events
from django.utils.translation import ugettext_lazy

parameters.register_user("LANG", type="list", deflt="en", 
                         label=ugettext_lazy("Prefered language"),
                         values=[("de", "deutsch"), ("en", "english"),
                                 ("es", "español"), ("fr", "français")],
                         help=ugettext_lazy("Prefered language to display pages"),
                         app="general")

@events.observe("GetStaticContent")
def get_static_content(user):
    return """<script type="text/javascript">
function chpasswordform_cb() {
    $(".submit").one('click', function(e) {
        simple_ajax_form_post(e, {
            formid: "chpasswordform",
            error_cb: chpasswordform_cb
        });
    });
}
</script>"""
