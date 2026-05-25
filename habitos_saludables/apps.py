"""
apps.py — Configuración de la app Hábitos Saludables SENA
"""

from django.apps import AppConfig


class HabitosSaludablesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'habitos_saludables'
    verbose_name = 'Hábitos Saludables SENA'