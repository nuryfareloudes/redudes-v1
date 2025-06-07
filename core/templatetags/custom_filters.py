from django import template

register = template.Library()

@register.filter
def multiply(value, arg):
    """Multiplica el valor por el argumento"""
    try:
        return float(value) * float(arg)
    except (ValueError, TypeError):
        return ''

@register.filter
def count_by_score(usuarios, max_score):
    """Cuenta usuarios con score menor o igual al valor dado"""
    try:
        max_score = float(max_score)
        return len([u for u in usuarios if getattr(u, 'score_combinado', 0) <= max_score])
    except (ValueError, TypeError):
        return 0

@register.filter
def count_by_min_score(usuarios, min_score):
    """Cuenta usuarios con score mayor o igual al valor dado"""
    try:
        min_score = float(min_score)
        return len([u for u in usuarios if getattr(u, 'score_combinado', 0) >= min_score])
    except (ValueError, TypeError):
        return 0

@register.filter
def subtract(value, arg):
    """Resta dos números"""
    try:
        return int(value) - int(arg)
    except (ValueError, TypeError):
        return 0


@register.filter
def filter_by_score_range(queryset, range_str):
    """
    Filtra por rango de score. Uso: queryset|filter_by_score_range:"0.5,0.7"
    """
    try:
        min_score, max_score = map(float, range_str.split(','))
        return queryset.filter(
            score_combinado__gt=min_score,
            score_combinado__lte=max_score
        )
    except:
        return queryset