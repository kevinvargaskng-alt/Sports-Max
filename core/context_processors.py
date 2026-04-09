# core/context_processors.py
from .constants import LISTA_PROGRAMAS

def programas_context(request):
    return {
        'PROGRAMAS_GLOBALES': LISTA_PROGRAMAS
    }