from django import template
from django.template.loader import render_to_string

register = template.Library()

@register.simple_tag
def domain_menu(domain_id, selection):
    return render_to_string('admin/domain_menu.html', 
                            {"selection" : selection,
                             "domain_id" : domain_id})


# class MyVar(template.Node):
#     def __init__(self, value, var_name):
#         self.var_name = var_name
#         self.value = value

#     def render(self, context):
#         context[self.var_name] = self.value
#         return ""

# import re

# @register.tag(name="var")
# def do_my_var(parser, token):
#     try:
#         tag_name, arg = token.contents.split(None, 1)
#     except ValueError:
#         raise template.TemplateSyntaxError, '%r tag requires arguments' \
#             % token.contents.split()[0]
#     m = re.search('(.*?) as (\w+)', arg)
#     if not m:
#         raise template.TemplateSyntaxError, "%r tag had invalid arguments" \
#             % tag_name
#     value, var_name = m.groups()
#     return MyVar(value, var_name)
