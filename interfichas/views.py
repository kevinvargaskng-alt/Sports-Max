from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TorneoInterfichas, EquipoInterfichas
import datetime

def interfichas_list(request):
    # Traemos los equipos para la tabla
    equipos = EquipoInterfichas.objects.select_related('torneo').all().order_by('-codigo_equipo_interfichas')
    
    if request.method == 'POST':
        try:
            nombre = request.POST.get('nombre')
            ficha_str = request.POST.get('ficha')
            programa = request.POST.get('programa')
            disciplina = request.POST.get('disciplina')
            fecha = request.POST.get('fecha')
            lugar = request.POST.get('lugar')

            # Lógica de Pasantes
            es_pasante = (programa == "Pasantes")
            ficha_final = 0 if es_pasante else int(ficha_str or 0)

            # Validación de duplicados
            if not es_pasante and EquipoInterfichas.objects.filter(ficha=ficha_final).exists():
                messages.error(request, f"La ficha {ficha_final} ya existe.")
                return redirect('interfichas')

            # 1. Crear Torneo (Con hora por defecto para evitar el IntegrityError)
            nuevo_torneo = TorneoInterfichas.objects.create(
                nombre_torneo=nombre,
                fecha_torneo_fichas=fecha,
                horario_torneo_fichas=datetime.time(0, 0),
                lugar=lugar,
                disciplina=disciplina
            )

            # 2. Crear Equipo
            EquipoInterfichas.objects.create(
                ficha=ficha_final,
                nombre_equipo=programa,
                disciplina=disciplina,
                torneo=nuevo_torneo
            )
            
            messages.success(request, "¡Guardado con éxito!")
            
        except Exception as e:
            messages.error(request, f"Error: {e}")
            
        return redirect('interfichas')
    
    return render(request, 'interfichas/interfichas.html', {'equipos': equipos})

# ESTO ARREGLA EL ERROR QUE MUESTRAS EN LA CONSOLA
def editar_torneo(request, id):
    # Por ahora solo redirige para que el servidor no falle
    # Más adelante puedes añadir la lógica para editar
    return redirect('interfichas')

# ESTO TAMBIÉN ES NECESARIO SI TIENES LA RUTA DE ELIMINAR
def eliminar_torneo(request, id):
    torneo = get_object_or_404(TorneoInterfichas, pk=id)
    torneo.delete()
    messages.success(request, "Registro eliminado.")
    return redirect('interfichas')