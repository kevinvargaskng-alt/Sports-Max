from django.shortcuts import render
from django.http import HttpResponse
from django.utils import timezone
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


# ═══════════════════════════════════════════════════════════
#  VISTAS LEGALES Y DE CUMPLIMIENTO
# ═══════════════════════════════════════════════════════════

def politica_privacidad(request):
    """Renderiza la Política de Privacidad y Tratamiento de Datos (Ley 1581 / RGPD)."""
    return render(request, 'legal/politica_privacidad.html')


def terminos_condiciones(request):
    """Renderiza los Términos y Condiciones de Uso del Sistema Deportivo."""
    return render(request, 'legal/terminos_condiciones.html')


def politica_cookies(request):
    """Renderiza la Política de Cookies informativa y panel de configuración."""
    return render(request, 'legal/politica_cookies.html')


# ═══════════════════════════════════════════════════════════
#  SEO TÉCNICO: ROBOTS.TXT Y SITEMAP.XML DINÁMICOS
# ═══════════════════════════════════════════════════════════

def robots_txt(request):
    """Genera dinámicamente el archivo robots.txt del sitio."""
    host = request.build_absolute_uri('/')[:-1]
    lines = [
        "User-agent: *",
        "Allow: /",
        "Disallow: /admin/",
        "Disallow: /api/",
        "Disallow: /perfil/",
        "Disallow: /gestionar-usuarios/",
        f"Sitemap: {host}/sitemap.xml",
    ]
    return HttpResponse("\n".join(lines), content_type="text/plain")


def sitemap_xml(request):
    """Genera dinámicamente el archivo sitemap.xml con metadatos y prioridades."""
    host = request.build_absolute_uri('/')[:-1]
    today = timezone.localdate().isoformat()

    urls = [
        {"loc": f"{host}/", "priority": "1.0", "changefreq": "daily"},
        {"loc": f"{host}/ayuda/", "priority": "0.8", "changefreq": "monthly"},
        {"loc": f"{host}/privacidad/", "priority": "0.5", "changefreq": "yearly"},
        {"loc": f"{host}/terminos/", "priority": "0.5", "changefreq": "yearly"},
        {"loc": f"{host}/cookies/", "priority": "0.5", "changefreq": "yearly"},
        {"loc": f"{host}/gimnasio/", "priority": "0.9", "changefreq": "daily"},
        {"loc": f"{host}/interfichas/", "priority": "0.9", "changefreq": "daily"},
        {"loc": f"{host}/inventario/", "priority": "0.8", "changefreq": "weekly"},
        {"loc": f"{host}/habitos/", "priority": "0.8", "changefreq": "weekly"},
    ]

    xml_lines = ['<?xml version="1.0" encoding="UTF-8"?>']
    xml_lines.append('<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">')
    for u in urls:
        xml_lines.append("  <url>")
        xml_lines.append(f"    <loc>{u['loc']}</loc>")
        xml_lines.append(f"    <lastmod>{today}</lastmod>")
        xml_lines.append(f"    <changefreq>{u['changefreq']}</changefreq>")
        xml_lines.append(f"    <priority>{u['priority']}</priority>")
        xml_lines.append("  </url>")
    xml_lines.append('</urlset>')

    return HttpResponse("\n".join(xml_lines), content_type="application/xml")


