from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from .models import TorneoInterfichas, EquipoInterfichas, Disciplina, JugadorEquipo
from django.contrib.auth.decorators import login_required
from .models import ResultadoTorneo
from datetime import date

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
            
            # Validar que no esté vacío
            if not nombre_disc:
                messages.error(request, "El nombre de la disciplina no puede estar vacío.")
                return redirect('interfichas')
            
            # Validar longitud
            if len(nombre_disc) > 50:
                messages.error(request, "El nombre de la disciplina no puede exceder 50 caracteres.")
                return redirect('interfichas')
            
            obj, created = Disciplina.objects.get_or_create(nombre_disciplina=nombre_disc)
            if created:
                messages.success(request, f"Disciplina '{nombre_disc}' creada exitosamente.")
            else:
                messages.info(request, f"La disciplina '{nombre_disc}' ya existe en el sistema.")
            return redirect('interfichas')

        # --- ACTUALIZADO: LÓGICA CREAR TORNEO (Seleccionando disciplina existente) ---
        elif accion == 'crear_torneo':
            # Validar y sanitizar datos
            nombre = request.POST.get('nombre', '').strip()
            fecha_str = request.POST.get('fecha', '').strip()
            lugar = request.POST.get('lugar', '').strip()
            id_disciplina = request.POST.get('disciplina_id', '').strip()
            
            # Validar campos requeridos
            if not nombre or not fecha_str or not lugar or not id_disciplina:
                messages.error(request, "Por favor, completa todos los campos requeridos.")
                return redirect('interfichas')
            
            # Validar longitud
            if len(nombre) > 100 or len(lugar) > 100:
                messages.error(request, "Nombre o lugar demasiado largo (máx. 100 caracteres).")
                return redirect('interfichas')
            
            # Validar fecha
            try:
                fecha = __import__('datetime').datetime.strptime(fecha_str, '%Y-%m-%d').date()
                if fecha < date.today():
                    messages.error(request, "La fecha del torneo debe ser igual o posterior a hoy.")
                    return redirect('interfichas')
            except (ValueError, TypeError):
                messages.error(request, "Formato de fecha inválido.")
                return redirect('interfichas')
            
            # Obtenemos la disciplina seleccionada del select
            disciplina_obj = get_object_or_404(Disciplina, pk=id_disciplina)
            
            TorneoInterfichas.objects.create(
                nombre_torneo=nombre,
                fecha_torneo_fichas=fecha,
                lugar=lugar,
                disciplina=disciplina_obj
            )
            messages.success(request, "Torneo programado correctamente.")
            return redirect('interfichas')

        # --- LÓGICA INSCRIBIR EQUIPO ---
        elif accion == 'inscribir_equipo':
            # Validar y sanitizar datos
            torneo_id = request.POST.get('torneo_id', '').strip()
            nombre_equipo = request.POST.get('nombre_equipo', '').strip()
            capitan = request.POST.get('capitan', '').strip()
            ficha = request.POST.get('ficha', '').strip()
            programa = request.POST.get('programa', '').strip()
            
            # Validar campos requeridos
            if not torneo_id or not nombre_equipo or not capitan or not ficha or not programa:
                messages.error(request, "Por favor, completa todos los campos requeridos.")
                return redirect('interfichas')
            
            # Validar longitudes
            if len(nombre_equipo) > 100 or len(capitan) > 100 or len(programa) > 150:
                messages.error(request, "Algunos campos exceden la longitud máxima permitida.")
                return redirect('interfichas')
            
            torneo_obj = get_object_or_404(TorneoInterfichas, pk=torneo_id)
            
            nuevo_equipo = EquipoInterfichas.objects.create(
                torneo=torneo_obj,
                nombre_equipo=nombre_equipo,
                capitan=capitan,
                ficha=int(ficha) if ficha.isdigit() else 0,
                programa=programa,
                disciplina=torneo_obj.disciplina,
                usuario_registra=request.user
            )

            # Procesar lista de jugadores
            jugadores_nombres = request.POST.getlist('jugadores[]')
            for nombre in jugadores_nombres:
                nombre_limpio = nombre.strip()
                if nombre_limpio:
                    JugadorEquipo.objects.create(nombre_completo=nombre_limpio, equipo=nuevo_equipo)
            
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


@login_required
def cerrar_torneo(request, codigo_torneo):
    torneo = get_object_or_404(TorneoInterfichas, codigo_torneo_fichas=codigo_torneo)

    if torneo.estado == 'cerrado':
        messages.error(request, 'Este torneo ya está cerrado.')
        return redirect('interfichas')

    equipos = torneo.equipos.all()

    if request.method == 'POST':
        ganador_id = request.POST.get('ganador_id')
        accion = request.POST.get('accion')

        if not ganador_id:
            messages.error(request, 'Debes seleccionar un equipo ganador.')
            return redirect('interfichas')

        ganador = get_object_or_404(EquipoInterfichas, id=ganador_id, torneo=torneo)

        resultado, _ = ResultadoTorneo.objects.update_or_create(
            torneo=torneo,
            defaults={'ganador': ganador}
        )

        if accion == 'archivar':
            resultado.archivado = True
            resultado.save()
            torneo.estado = 'cerrado'
            torneo.save()
            messages.success(request, f'Torneo "{torneo.nombre_torneo}" cerrado y archivado correctamente.')
            return redirect('interfichas')

        messages.success(request, f'¡{ganador.nombre_equipo} declarado como ganador!')
        return redirect('interfichas')

    return redirect('interfichas')
