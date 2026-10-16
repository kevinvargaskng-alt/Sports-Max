"""
Parcha reporte_torneo.html de forma confiable usando marcadores exactos.
Reemplaza la seccion de equipos+firmas por equipos-con-grupo + cronograma + firmas.
"""
import re

filepath = r'c:\Users\varga\OneDrive\Desktop\Django\interfichas\templates\interfichas\reporte_torneo.html'
with open(filepath, encoding='utf-8') as f:
    content = f.read()

print(f'Lineas originales: {len(content.splitlines())}')

# Marcador de inicio: el comentario que abre la seccion de equipos
MARKER_START = '            <!-- EQUIPOS PARTICIPANTES Y PLANILLAS -->'
# Marcador de fin: el cierre del endblock
MARKER_END = '{% endblock %}\r\n'

idx_start = content.find(MARKER_START)
idx_end   = content.rfind(MARKER_END)  # ultimo endblock

if idx_start == -1:
    print('ERROR: marcador de inicio no encontrado')
    exit(1)
if idx_end == -1:
    print('ERROR: endblock no encontrado')
    exit(1)

print(f'Reemplazando desde pos {idx_start} hasta {idx_end + len(MARKER_END)}')

NUEVA_SECCION = r"""            <!-- EQUIPOS PARTICIPANTES CON GRUPO -->
            <div class="mb-5">
                <div class="reporte-section-title">
                    <i class="fas fa-users"></i> Equipos Participantes
                </div>
                <div class="table-responsive">
                    <table class="table-reporte tabla-equipos-reporte">
                        <thead>
                            <tr>
                                <th style="width:28px;" class="text-center">#</th>
                                <th>Equipo</th>
                                <th class="text-center" style="width:70px;">Grupo</th>
                                <th>Ficha</th>
                                <th>Capitán</th>
                                <th>Programa de Formación</th>
                                <th class="text-center">Jugadores</th>
                                <th class="text-center">Planilla</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for eq in equipos_con_grupo %}
                            <tr>
                                <td class="text-center text-white-50 small">{{ forloop.counter }}</td>
                                <td class="fw-bold text-white">
                                    <i class="fas fa-shield-alt text-info me-2"></i>{{ eq.nombre_equipo }}
                                </td>
                                <td class="text-center">
                                    {% if eq.nombre_grupo %}
                                    <span class="badge fw-bold px-2 py-1" style="background:rgba(88,166,255,0.15);border:1px solid rgba(88,166,255,0.4);color:#58a6ff;">Gr.{{ eq.nombre_grupo }}</span>
                                    {% else %}<span class="text-white-50">—</span>{% endif %}
                                </td>
                                <td><span class="badge bg-secondary text-white badge-ficha-print">{{ eq.ficha }}</span></td>
                                <td><strong class="text-white">{{ eq.capitan }}</strong></td>
                                <td class="text-white-50 small">{{ eq.programa }}</td>
                                <td class="text-center">
                                    <span class="badge bg-dark border border-secondary text-info fw-bold">{{ eq.jugadores.count }}</span>
                                </td>
                                <td class="text-center">
                                    {% if eq.planilla_inscripcion %}
                                    <a href="{{ eq.planilla_inscripcion.url }}" target="_blank" class="badge-planilla-ok btn btn-sm btn-outline-success py-1 px-2 fw-bold text-decoration-none" style="font-size:0.78rem;">
                                        <i class="fas fa-file-pdf text-danger"></i> Ver
                                    </a>
                                    {% else %}
                                    <span class="badge-sin-planilla badge bg-dark border border-secondary text-white-50">Sin planilla</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% empty %}
                            <tr><td colspan="8" class="text-center text-white-50 py-4">No hay equipos inscritos.</td></tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- CRONOGRAMA COMPLETO FASE DE GRUPOS -->
            {% if cronograma_grupo %}
            <div class="mb-5">
                <div class="reporte-section-title">
                    <i class="fas fa-calendar-alt"></i> Cronograma — Fase de Grupos
                </div>
                <p class="text-white-50 small mb-3">
                    <i class="fas fa-check-circle text-success me-1"></i>Jugados primero &nbsp;·&nbsp;
                    <i class="fas fa-clock text-warning me-1"></i>Pendientes al final &nbsp;·&nbsp;
                    1 partido/día hábil (lun–vie), grupos intercalados
                </p>
                <div class="table-responsive">
                    <table class="table-reporte" id="tabla-cronograma">
                        <thead>
                            <tr>
                                <th class="text-center" style="width:32px;">#</th>
                                <th style="width:100px;">Fecha</th>
                                <th class="text-center" style="width:40px;">Día</th>
                                <th class="text-center" style="width:65px;">Grupo</th>
                                <th>Partido</th>
                                <th class="text-center" style="width:100px;">Resultado</th>
                                <th class="text-center" style="width:85px;">Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in cronograma_grupo %}
                            <tr {% if p.jugado %}style="background:rgba(63,185,80,0.06);"{% endif %}>
                                <td class="text-center text-white-50 small">{{ forloop.counter }}</td>
                                <td>
                                    {% if p.fecha_partido %}
                                    <span class="fw-semibold text-white" style="font-size:0.85rem;">{{ p.fecha_partido|date:"d/m/Y" }}</span>
                                    {% else %}<span class="text-white-50 small">Por asignar</span>{% endif %}
                                </td>
                                <td class="text-center small text-white-50">
                                    {% if p.fecha_partido %}{% with wd=p.fecha_partido.weekday %}{% if wd == 0 %}Lun{% elif wd == 1 %}Mar{% elif wd == 2 %}Mié{% elif wd == 3 %}Jue{% elif wd == 4 %}Vie{% elif wd == 5 %}Sáb{% else %}Dom{% endif %}{% endwith %}{% endif %}
                                </td>
                                <td class="text-center">
                                    <span class="badge fw-bold" style="background:rgba(88,166,255,0.15);border:1px solid rgba(88,166,255,0.4);color:#58a6ff;">Gr.{{ p.grupo.nombre_grupo }}</span>
                                </td>
                                <td>
                                    <span class="fw-bold text-white">{{ p.equipo_local.nombre_equipo }}</span>
                                    <span class="text-white-50 small mx-1">vs</span>
                                    <span class="fw-bold text-white">{{ p.equipo_visitante.nombre_equipo }}</span>
                                </td>
                                <td class="text-center">
                                    {% if p.jugado %}
                                    <span class="badge bg-primary fw-bold" style="font-size:0.95rem;letter-spacing:1px;">{{ p.goles_local }} — {{ p.goles_visitante }}</span>
                                    {% else %}<span class="text-white-50">—</span>{% endif %}
                                </td>
                                <td class="text-center">
                                    {% if p.jugado %}
                                    <span class="badge bg-success text-white" style="font-size:0.7rem;"><i class="fas fa-check me-1"></i>Jugado</span>
                                    {% else %}
                                    <span class="badge bg-dark border border-secondary text-warning" style="font-size:0.7rem;"><i class="fas fa-clock me-1"></i>Pendiente</span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>
            {% endif %}

            <!-- FIRMAS INSTITUCIONALES (A TODO COLOR EN IMPRESIÓN) -->
            <div class="firmas-reporte row g-4 text-center">
                <div class="col-6">
                    <div class="border-top border-secondary pt-2 mx-auto" style="max-width: 260px;">
                        <p class="mb-0 fw-bold small text-white">Coordinación de Deportes</p>
                        <small class="text-white-50">Bienestar al Aprendiz SENA</small>
                    </div>
                </div>
                <div class="col-6">
                    <div class="border-top border-secondary pt-2 mx-auto" style="max-width: 260px;">
                        <p class="mb-0 fw-bold small text-white">Administrador del Torneo</p>
                        <small class="text-white-50">Plataforma Sports-Max</small>
                    </div>
                </div>
            </div>

        </div>
    </div>

</div>
{% endblock %}
"""

nueva_content = content[:idx_start] + NUEVA_SECCION

with open(filepath, 'w', encoding='utf-8') as f:
    f.write(nueva_content)

lineas = len(nueva_content.splitlines())
print(f'Lineas finales: {lineas}')
print('Template parcheada exitosamente!')
