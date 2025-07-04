from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    return dictionary.get(key)

@register.filter
def sub(value, arg):
    """Soustraction dans les templates : {{ value|sub:arg }}"""
    try:
        return float(value) - float(arg)
    except (ValueError, TypeError):
        return 0

@register.filter
def sum_attr(queryset, attr_name):
    """Somme les valeurs d'un attribut donné"""
    return sum(getattr(obj, attr_name, 0) for obj in queryset)

@register.filter
def paid_count(queryset):
    """Compte les commandes payées"""
    return sum(1 for cmd in queryset if cmd.payee)

@register.filter
def unpaid_sum(queryset):
    """Somme les totaux des commandes non payées"""
    return sum(cmd.total for cmd in queryset if not cmd.payee)

@register.filter
def total_par_livreur(commandes):
    """Calcule le total des commandes pour un livreur"""
    return sum(cmd.total for cmd in commandes)

@register.filter
def commandes_payees(commandes):
    """Compte le nombre de commandes payées"""
    return sum(1 for cmd in commandes if cmd.payee)

@register.filter
def percentof(value, total):
    try:
        if total == 0:
            return 0
        return "%.1f" % ((float(value) / float(total)) * 100)
    except (ValueError, TypeError):
        return 0