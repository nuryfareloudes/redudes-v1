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
    """Cuenta usuarios con score de red neuronal menor o igual al valor dado"""
    try:
        max_score = float(max_score)
        return len([u for u in usuarios if getattr(u, 'score_nn', 0) <= max_score])
    except (ValueError, TypeError):
        return 0

@register.filter
def count_by_min_score(usuarios, min_score):
    """Cuenta usuarios con score de red neuronal mayor o igual al valor dado"""
    try:
        min_score = float(min_score)
        return len([u for u in usuarios if getattr(u, 'score_nn', 0) >= min_score])
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
    Filtra por rango de score de red neuronal. Uso: queryset|filter_by_score_range:"0.5,0.7"
    """
    try:
        min_score, max_score = map(float, range_str.split(','))
        return queryset.filter(
            score_nn__gt=min_score,
            score_nn__lte=max_score
        )
    except:
        return queryset

@register.filter
def count_alta_confianza(usuarios):
    """Cuenta usuarios con alta confianza (score_nn >= 0.7)"""
    try:
        return len([u for u in usuarios if getattr(u, 'score_nn', 0) >= 0.7])
    except:
        return 0

@register.filter
def count_media_confianza(usuarios):
    """Cuenta usuarios con media confianza (0.5 <= score_nn < 0.7)"""
    try:
        return len([u for u in usuarios if 0.5 <= getattr(u, 'score_nn', 0) < 0.7])
    except:
        return 0

@register.filter
def count_baja_confianza(usuarios):
    """Cuenta usuarios con baja confianza (score_nn < 0.5)"""
    try:
        return len([u for u in usuarios if getattr(u, 'score_nn', 0) < 0.5])
    except:
        return 0