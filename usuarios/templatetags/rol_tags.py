"""
usuarios/templatetags/rol_tags.py
CP-16: Template tags para el sistema de roles
"""
from django import template
from core.permisos import ROL_ICONOS, ROL_COLORES, ROLES

register = template.Library()


@register.filter(name='rol_icono')
def rol_icono(rol):
    """Retorna la clase de icono FontAwesome para un rol dado."""
    return ROL_ICONOS.get(rol, 'fa-user')


@register.filter(name='rol_color')
def rol_color(rol):
    """Retorna el color Bootstrap para el badge de un rol."""
    return ROL_COLORES.get(rol, 'secondary')


@register.filter(name='rol_label')
def rol_label(rol):
    """Retorna la etiqueta legible de un rol."""
    return ROLES.get(rol, rol.capitalize())


@register.filter(name='get_item')
def get_item(dictionary, key):
    """Permite acceder a un dict con clave dinámica en templates."""
    return dictionary.get(key, 0)
