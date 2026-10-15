import os
import sys
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import django

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'core.settings')
django.setup()

from interfichas.models import TorneoInterfichas, PartidoInterfichas

torneo = TorneoInterfichas.objects.filter(nombre_torneo__icontains='mundialito').first()
if not torneo:
    torneo = TorneoInterfichas.objects.first()

print(f"Torneo: {torneo.nombre_torneo} (ID: {torneo.id})")
grupos = torneo.grupos.all()
for g in grupos:
    eqs = [eq.nombre_equipo for eq in g.equipos.all()]
    print(f"  Grupo {g.nombre_grupo} ({len(eqs)} equipos): {', '.join(eqs)}")

partidos = PartidoInterfichas.objects.filter(torneo=torneo, fase='grupo').order_by('fecha_partido', 'id')
print(f"\nTotal partidos fase de grupos: {partidos.count()}")
jugados = [p for p in partidos if p.jugado]
pendientes = [p for p in partidos if not p.jugado]
print(f"  Jugados ({len(jugados)}):")
for p in jugados:
    f = p.fecha_partido.strftime('%d/%m/%Y') if p.fecha_partido else 'Sin fecha'
    print(f"    [{f}] Grupo {p.grupo.nombre_grupo}: {p.equipo_local.nombre_equipo} {p.goles_local} - {p.goles_visitante} {p.equipo_visitante.nombre_equipo}")

print(f"  Primeros 10 pendientes ({len(pendientes)} total):")
for p in pendientes[:10]:
    f = p.fecha_partido.strftime('%a %d/%m/%Y') if p.fecha_partido else 'Sin fecha'
    print(f"    [{f}] Grupo {p.grupo.nombre_grupo}: {p.equipo_local.nombre_equipo} vs {p.equipo_visitante.nombre_equipo}")
