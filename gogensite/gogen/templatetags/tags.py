from django import template

register = template.Library()

@register.filter(name='zip')
def zip_lists(a, b):
  return zip(a, b)

@register.filter(name='tuplezip')
def tuple_zip_lists(a):
  return zip(*a)

@register.filter(name='intcomma')
def int_comma(a):
  try:
    return f"{int(a):,d}"
  except ValueError:
    return a
