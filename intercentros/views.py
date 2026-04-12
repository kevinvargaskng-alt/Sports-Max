from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from .models import TorneoIntercentros, EquipoIntercentros

@login_required
def intercentros_list(request):
    # Traemos las convocatorias de torneos (Intercentros)
    torneos = TorneoIntercentros.objects.all().order_by('-fecha_torneo')
    
    # Traemos las postulaciones del usuario logueado (Opcional si tienes el modelo)
    # mis_postulaciones = EquipoIntercentros.objects.filter(numero_documento=request.user.numero_documento)

    if request.method == 'POST':
        accion = request.POST.get('accion')

        # 1. ACCIÓN: El aprendiz se postula automáticamente
        if accion == 'inscribir_aprendiz':
            disciplina = request.POST.get('disciplina')
            
            # Aquí guardarías en tu modelo de EquipoIntercentros
            # EquipoIntercentros.objects.create(
            #     nombres=request.user.first_name,
            #     apellidos=request.user.last_name,
            #     documento=request.user.numero_documento,
            #     ficha=request.user.ficha,
            #     programa=request.user.programa_formacion,
            #     disciplina=disciplina
            # )
            
            messages.success(request, f"¡Postulación para {disciplina} enviada exitosamente!")
            return redirect('intercentros')

        # 2. ACCIÓN: Crear torneo (Uso administrativo)
        elif accion == 'crear_torneo':
            TorneoIntercentros.objects.create(
                nombre_torneo=request.POST.get('nombre'),
                fecha_torneo=request.POST.get('fecha'),
                lugar=request.POST.get('lugar'),
                disciplina=request.POST.get('disciplina')
            )
            messages.success(request, "Nueva convocatoria Intercentros publicada.")
            return redirect('intercentros')

    return render(request, 'intercentros/intercentros.html', {
        'torneos': torneos,
        'ahora': timezone.localtime(timezone.now()),
    })

@login_required
def eliminar_torneo(request, id):
    torneo = get_object_or_404(TorneoIntercentros, codigo_torneo_centro=id)
    torneo.delete()
    messages.warning(request, "Convocatoria eliminada correctamente.")
    return redirect('intercentros')