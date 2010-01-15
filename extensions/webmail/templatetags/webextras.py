from django import template
from django.template.loader import render_to_string
from django.utils.translation import ugettext as _
from django.core.urlresolvers import reverse
from mailng.extensions import webmail

register = template.Library()

@register.simple_tag
def viewm_menu(selection, mail_id, page_id, perms):   
    entries = [
        {"name" : "back",
         "url" : reverse(webmail.main.index) + "?page=%s" % page_id,
         "img" : "/static/pics/back.png",
         "label" : _("Back to list")},
        ]
    
    return render_to_string('main/menu.html', 
                            {"selection" : selection, "entries" : entries, 
                             "perms" : perms})
