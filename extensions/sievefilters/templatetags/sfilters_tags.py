from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from modoboa.extensions.sievefilters import views

register = template.Library()

from modoboa.lib import static_url

@register.simple_tag
def sfilters_menu(user):
    entries = [
        {"name"  : "newfilterset",
         "img"   : static_url("pics/add.png"),
         "label" : _("New filters set"),
         "url" : reverse(views.new_filters_set),
         "class" : "boxed",
         "rel" : "{handler:'iframe',size:{x:300,y:170}}"
         },
        {"name" : "savescript",
         "img" : static_url("pics/save.png"),
         "label" : _("Save filters set"),
         "url" : ""},
        {"name" : "activatescript",
         "img" : static_url("pics/active.png"),
         "label" : _("Activate filters set"),
         "url" : reverse(views.activate_filters_set)},
        {"name" : "deletescript",
         "img" : static_url("pics/remove.png"),
         "label" : _("Remove filters set"),
         "url" : reverse(views.delete_filters_set),},
        {"name" : "downloadscript",
         "img" : static_url("pics/download.png"),
         "label" : _("Download"),
         "url" : reverse(views.download_filters_set)}
        ]

    return render_to_string('common/menulist.html', 
                            {"entries" : entries, "user" : user})
