import json
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TorneoInterfichas, EquipoInterfichas, Disciplina, JugadorEquipo

# VISTA PRINCIPAL (LISTAR, CREAR TORNEO E INSCRIBIR EQUIPO)
def interfichas_list(request):
    # Traemos equipos con su relación torneo para la tabla unificada
    equipos = EquipoInterfichas.objects.select_related('torneo', 'disciplina').all()
    disciplinas = Disciplina.objects.all()
    torneos_disponibles = TorneoInterfichas.objects.filter(estado='Activo')

    if request.method == 'POST':
        accion = request.POST.get('accion_tipo') # Usaremos un campo hidden en el HTML

        # 1. LÓGICA PARA CREAR TORNEO
        if accion == 'crear_torneo':
            try:
                # Si usas ForeignKey para disciplina:
                disc_id = request.POST.get('disciplina')
                disciplina_obj = get_object_or_404(Disciplina, id=disc_id)
                
                TorneoInterfichas.objects.create(
                    nombre_torneo=request.POST.get('nombre'),
                    fecha_torneo_fichas=request.POST.get('fecha'),
                    horario_torneo_fichas=request.POST.get('hora', '00:00'),
                    lugar=request.POST.get('lugar'),
                    disciplina=disciplina_obj
                )
                messages.success(request, "Torneo creado exitosamente.")
            except Exception as e:
                messages.error(request, f"Error al crear torneo: {e}")

        # 2. LÓGICA PARA INSCRIBIR EQUIPO (Y SUS JUGADORES)
        elif accion == 'inscribir_equipo':
            try:
                torneo_id = request.POST.get('torneo_id')
                torneo_obj = get_object_or_404(TorneoInterfichas, pk=torneo_id)
                
                # Crear el equipo
                nuevo_equipo = EquipoInterfichas.objects.create(
                    nombre_equipo=request.POST.get('nombre_equipo'),
                    ficha=request.POST.get('ficha'),
                    programa=request.POST.get('programa'),
                    disciplina=torneo_obj.disciplina,
                    torneo=torneo_obj
                )

                # Procesar lista de jugadores (enviada como JSON desde JS o inputs múltiples)
                jugadores_nombres = request.POST.getlist('jugadores[]')
                for nombre in jugadores_nombres:
                    if nombre.strip():
                        JugadorEquipo.objects.create(nombre_completo=nombre, equipo=nuevo_equipo)
                
                messages.success(request, f"Equipo {nuevo_equipo.nombre_equipo} inscrito correctamente.")
            except Exception as e:
                messages.error(request, f"Error en la inscripción: {e}")

        return redirect('interfichas')
    
    context = {
        'equipos': equipos,
        'disciplinas': disciplinas,
        'torneos_activos': torneos_disponibles
    }
    return render(request, 'interfichas/interfichas.html', context)

# ELIMINAR
def eliminar_torneo(request, id):
    torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=id)
    nombre = torneo.nombre_torneo
    torneo.delete()
    messages.warning(request, f"Torneo '{nombre}' eliminado.")
    return redirect('interfichas')

# EDITAR (VÍA AJAX O POST DIRECTO)
def editar_torneo(request):
    if request.method == 'POST':
        id_torneo = request.POST.get('id_editar')
        torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=id_torneo)
        
        torneo.nombre_torneo = request.POST.get('nombre')
        # Si usas ForeignKey:
        disc_id = request.POST.get('disciplina')
        torneo.disciplina = get_object_or_404(Disciplina, id=disc_id)
        
        torneo.save()
        messages.info(request, "Registro actualizado correctamente.")
    return redirect('interfichas')