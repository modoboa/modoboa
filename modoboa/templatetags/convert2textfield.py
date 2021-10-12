from django import template
  
register = template.Library()

@register.filter
def convert2textfield(value):

    arr = value.split('"')[1::2]
    for index, item in enumerate(arr):
        arr[index] = f'<input type="text" name="str{index}" value="{item}" size="100"><br/>'

    string=''.join(arr)

    return string
