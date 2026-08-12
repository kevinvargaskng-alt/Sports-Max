from django.shortcuts import render
from interfichas.models import EquipoInterfichas, Disciplina, PartidoInterfichas, TorneoInterfichas
from usuarios.models import Usuario


def inicio(request):
    """Renderiza la página principal (Hero Section)"""
    
    # Valores por defecto en caso de error o base de datos vacía
    equipos_inscritos = 0
    disciplinas_activas = 0
    total_aprendices = 0
    jornadas_jugadas = 0
    escenarios_deportivos = 0

    try:
        equipos_inscritos = EquipoInterfichas.objects.count()
    except Exception:
        pass

    try:
        # Disciplinas activas: que tengan torneos activos
        disciplinas_activas = Disciplina.objects.filter(torneos__estado='activo').distinct().count()
        if disciplinas_activas == 0:
            disciplinas_activas = Disciplina.objects.count()
    except Exception:
        pass

    try:
        # total de aprendices registrados en el sistema
        total_aprendices = Usuario.objects.filter(rol='aprendiz').count()
    except Exception:
        pass

    try:
        # partidos jugados
        jornadas_jugadas = PartidoInterfichas.objects.filter(jugado=True).count()
    except Exception:
        pass

    try:
        # escenarios deportivos: lugares distintos de torneos + gimnasio
        lugares_torneo = TorneoInterfichas.objects.exclude(lugar='').values_list('lugar', flat=True).distinct().count()
        escenarios_deportivos = lugares_torneo + 1  # Se suma 1 por el gimnasio
        if escenarios_deportivos == 1 and lugares_torneo == 0:
            # Fallback en caso de que no haya torneos aún
            escenarios_deportivos = 2
    except Exception:
        pass

    context = {
        # Usamos el sistema nativo de Django para saber si está logueado
        'aprendiz_logueado': request.user.is_authenticated,
        'nombre_usuario': request.user.get_full_name() if request.user.is_authenticated else '',
        'stats': {
            'equipos_inscritos': equipos_inscritos,
            'disciplinas_activas': disciplinas_activas,
            'total_aprendices': total_aprendices,
            'jornadas_jugadas': jornadas_jugadas,
            'escenarios_deportivos': escenarios_deportivos,
        }
    }
    return render(request, 'inicio.html', context)



def ayuda(request):
    """Renderiza el centro de ayuda e instructivo de usuario."""
    return render(request, 'ayuda.html')

