from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TorneoInterfichas, EquipoInterfichas, Disciplina, JugadorEquipo
from django.contrib.auth.decorators import login_required

@login_required
def interfichas_list(request):
    # Traemos todos los torneos para la tabla de arriba
    torneos = TorneoInterfichas.objects.all().order_by('-fecha_torneo_fichas')
    
    # Traemos todos los equipos para la tabla de abajo
    equipos = EquipoInterfichas.objects.select_related('torneo', 'disciplina').all()
    
    # Traemos todas las disciplinas para los selects de los modales
    disciplinas = Disciplina.objects.all().order_by('nombre_disciplina')

    if request.method == 'POST':
        accion = request.POST.get('accion_tipo')

        # --- NUEVO: LÓGICA PARA CREAR SOLO DISCIPLINA (Historia de Usuario) ---
        if accion == 'crear_disciplina_unica':
            nombre_disc = request.POST.get('nombre_disciplina', '').strip()
            if nombre_disc:
                obj, created = Disciplina.objects.get_or_create(nombre_disciplina=nombre_disc)
                if created:
                    messages.success(request, f"Disciplina '{nombre_disc}' creada exitosamente.")
                else:
                    messages.info(request, f"La disciplina '{nombre_disc}' ya existe en el sistema.")
            return redirect('interfichas')

        # --- ACTUALIZADO: LÓGICA CREAR TORNEO (Seleccionando disciplina existente) ---
        elif accion == 'crear_torneo':
            id_disciplina = request.POST.get('disciplina_id')
            # Obtenemos la disciplina seleccionada del select
            disciplina_obj = get_object_or_404(Disciplina, pk=id_disciplina)
            
            TorneoInterfichas.objects.create(
                nombre_torneo=request.POST.get('nombre'),
                fecha_torneo_fichas=request.POST.get('fecha'),
                lugar=request.POST.get('lugar'),
                disciplina=disciplina_obj
            )
            messages.success(request, "Torneo programado correctamente.")
            return redirect('interfichas')

        # --- LÓGICA INSCRIBIR EQUIPO ---
        elif accion == 'inscribir_equipo':
            torneo_id = request.POST.get('torneo_id')
            torneo_obj = get_object_or_404(TorneoInterfichas, pk=torneo_id)
            
            nuevo_equipo = EquipoInterfichas.objects.create(
                torneo=torneo_obj,
                nombre_equipo=request.POST.get('nombre_equipo'),
                capitan=request.POST.get('capitan'),
                ficha=request.POST.get('ficha'),
                programa=request.POST.get('programa'),
                disciplina=torneo_obj.disciplina,
                usuario_registra=request.user
            )

            # Procesar lista de jugadores
            jugadores_nombres = request.POST.getlist('jugadores[]')
            for nombre in jugadores_nombres:
                if nombre.strip():
                    JugadorEquipo.objects.create(nombre_completo=nombre, equipo=nuevo_equipo)
            
            messages.success(request, f"Equipo '{nuevo_equipo.nombre_equipo}' inscrito exitosamente.")
            return redirect('interfichas')

    return render(request, 'interfichas/interfichas.html', {
        'torneos': torneos,
        'equipos': equipos,
        'disciplinas': disciplinas
    })

@login_required
def eliminar_torneo(request, id):
    torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=id)
    torneo.delete()
    messages.warning(request, "Torneo eliminado correctamente.")
    return redirect('interfichas')

@login_required
def editar_torneo(request):
    if request.method == 'POST':
        id_torneo = request.POST.get('id_editar')
        torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=id_torneo)
        
        torneo.nombre_torneo = request.POST.get('nombre')
        id_disciplina = request.POST.get('disciplina_id')
        disciplina_obj = get_object_or_404(Disciplina, pk=id_disciplina)
        
        torneo.disciplina = disciplina_obj
        torneo.save()
        messages.info(request, "Torneo actualizado.")
    return redirect('interfichas')