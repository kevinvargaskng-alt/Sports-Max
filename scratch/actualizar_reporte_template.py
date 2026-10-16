"""
Script para actualizar interfichas/templates/interfichas/reporte_torneo.html
de forma limpia y segura.
"""
import sys
from pathlib import Path

template_path = Path(r"c:\Users\varga\OneDrive\Desktop\Django\interfichas\templates\interfichas\reporte_torneo.html")
content = template_path.read_text(encoding="utf-8")

# 1. Agregar estilos CSS para cronograma y grupos
css_to_add = """
    /* Estilos de Cronograma de Partidos en Pantalla */
    .tabla-cronograma-reporte {
        width: 100%;
        border-collapse: collapse;
        font-size: 0.88rem;
    }
    .fila-partido-jugado {
        background: rgba(16, 185, 129, 0.04);
    }
    .badge-grupo-tag {
        font-size: 0.75rem;
        font-weight: 700;
        padding: 3px 8px;
        border-radius: 6px;
    }
    .badge-grupo-A { background: rgba(2, 132, 199, 0.2); color: #38bdf8; border: 1px solid #0284c7; }
    .badge-grupo-B { background: rgba(16, 185, 129, 0.2); color: #34d399; border: 1px solid #10b981; }
    .badge-grupo-C { background: rgba(245, 158, 11, 0.2); color: #fbbf24; border: 1px solid #f59e0b; }
    .badge-grupo-D { background: rgba(139, 92, 246, 0.2); color: #a78bfa; border: 1px solid #8b5cf6; }

    /* Estilos de Impresión para Cronograma y Grupos */
    .tabla-cronograma-reporte {
        page-break-inside: auto;
    }
    .tabla-cronograma-reporte tr {
        page-break-inside: avoid;
    }
    .tabla-cronograma-reporte thead th {
        background: #1e293b !important;
        color: #ffffff !important;
        font-weight: 800 !important;
    }
    .badge-grupo-print-A { background: #e0f2fe !important; color: #0369a1 !important; border: 1px solid #bae6fd !important; }
    .badge-grupo-print-B { background: #ecfdf5 !important; color: #047857 !important; border: 1px solid #a7f3d0 !important; }
    .badge-grupo-print-C { background: #fffbeb !important; color: #b45309 !important; border: 1px solid #fde68a !important; }
    .badge-grupo-print-D { background: #f5f3ff !important; color: #6d28d9 !important; border: 1px solid #ddd6fe !important; }
"""

# Insertar CSS antes de </style>
if "/* Estilos de Cronograma de Partidos en Pantalla */" not in content:
    content = content.replace("</style>", css_to_add + "\n</style>", 1)

# 2. Reemplazar la tabla de equipos para mostrar el Grupo
old_equipos_section = """            <!-- EQUIPOS PARTICIPANTES Y PLANILLAS -->
            <div class="mb-4">
                <div class="reporte-section-title">
                    <i class="fas fa-users"></i> Equipos Inscritos y Planillas Físicas
                </div>

                <div class="table-responsive">
                    <table class="table-reporte tabla-equipos-reporte">
                        <thead>
                            <tr>
                                <th>Equipo</th>
                                <th>Ficha</th>
                                <th>Capitán</th>
                                <th>Programa de Formación</th>
                                <th class="text-center">Jugadores</th>
                                <th class="text-center">Planilla de Inscripción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for eq in equipos %}
                            <tr>
                                <td class="fw-bold text-white">
                                    <i class="fas fa-shield-alt text-info me-2"></i>{{ eq.nombre_equipo }}
                                </td>
                                <td>
                                    <span class="badge bg-secondary text-white badge-ficha-print">{{ eq.ficha }}</span>
                                </td>
                                <td><strong class="text-white">{{ eq.capitan }}</strong></td>
                                <td class="text-white-50 small">{{ eq.programa }}</td>
                                <td class="text-center">
                                    <span class="badge bg-dark border border-secondary text-info fw-bold">
                                        {{ eq.jugadores.count }}
                                    </span>
                                </td>
                                <td class="text-center">
                                    {% if eq.planilla_inscripcion %}
                                    <a href="{{ eq.planilla_inscripcion.url }}" target="_blank" class="badge-planilla-ok btn btn-sm btn-outline-success py-1 px-3 fw-bold text-decoration-none">
                                        <i class="fas fa-file-pdf text-danger"></i> Planilla Adjunta
                                    </a>
                                    {% else %}
                                    <span class="badge-sin-planilla badge bg-dark border border-secondary text-white-50">
                                        Sin planilla física
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="6" class="text-center text-white-50 py-4">No hay equipos inscritos en este torneo.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>"""

new_equipos_and_cronograma_section = """            <!-- EQUIPOS PARTICIPANTES Y GRUPOS -->
            <div class="mb-5">
                <div class="reporte-section-title">
                    <i class="fas fa-users"></i> Equipos Inscritos y Distribución por Grupos
                </div>

                <div class="table-responsive">
                    <table class="table-reporte tabla-equipos-reporte">
                        <thead>
                            <tr>
                                <th>Equipo</th>
                                <th class="text-center">Grupo</th>
                                <th>Ficha</th>
                                <th>Capitán</th>
                                <th>Programa de Formación</th>
                                <th class="text-center">Jugadores</th>
                                <th class="text-center">Planilla de Inscripción</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for eq in equipos_con_grupo %}
                            <tr>
                                <td class="fw-bold text-white">
                                    <i class="fas fa-shield-alt text-info me-2"></i>{{ eq.nombre_equipo }}
                                </td>
                                <td class="text-center">
                                    {% if eq.nombre_grupo %}
                                    <span class="badge badge-grupo-tag badge-grupo-{{ eq.nombre_grupo }} badge-grupo-print-{{ eq.nombre_grupo }}">
                                        Grupo {{ eq.nombre_grupo }}
                                    </span>
                                    {% else %}
                                    <span class="badge bg-secondary text-white-50 small">Sin Grupo</span>
                                    {% endif %}
                                </td>
                                <td>
                                    <span class="badge bg-secondary text-white badge-ficha-print">{{ eq.ficha }}</span>
                                </td>
                                <td><strong class="text-white">{{ eq.capitan }}</strong></td>
                                <td class="text-white-50 small">{{ eq.programa }}</td>
                                <td class="text-center">
                                    <span class="badge bg-dark border border-secondary text-info fw-bold">
                                        {{ eq.jugadores.count }}
                                    </span>
                                </td>
                                <td class="text-center">
                                    {% if eq.planilla_inscripcion %}
                                    <a href="{{ eq.planilla_inscripcion.url }}" target="_blank" class="badge-planilla-ok btn btn-sm btn-outline-success py-1 px-3 fw-bold text-decoration-none">
                                        <i class="fas fa-file-pdf text-danger"></i> Planilla Adjunta
                                    </a>
                                    {% else %}
                                    <span class="badge-sin-planilla badge bg-dark border border-secondary text-white-50">
                                        Sin planilla física
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="7" class="text-center text-white-50 py-4">No hay equipos inscritos en este torneo.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- CRONOGRAMA OFICIAL DE PARTIDOS (ORDEN CRONOLÓGICO - JUGADOS PRIMERO) -->
            <div class="mb-5">
                <div class="reporte-section-title">
                    <i class="fas fa-calendar-alt"></i> Cronograma Oficial de Partidos — Fase de Grupos
                </div>

                <div class="table-responsive">
                    <table class="table-reporte tabla-cronograma-reporte">
                        <thead>
                            <tr>
                                <th class="text-center" style="width: 45px;">#</th>
                                <th style="width: 150px;">Fecha / Día</th>
                                <th class="text-center" style="width: 105px;">Grupo</th>
                                <th class="text-end" style="width: 32%;">Equipo Local</th>
                                <th class="text-center" style="width: 110px;">Resultado</th>
                                <th style="width: 32%;">Equipo Visitante</th>
                                <th class="text-center" style="width: 115px;">Estado</th>
                            </tr>
                        </thead>
                        <tbody>
                            {% for p in cronograma_grupo %}
                            <tr class="{% if p.jugado %}fila-partido-jugado{% else %}fila-partido-pendiente{% endif %}">
                                <td class="text-center text-white-50 small">{{ forloop.counter }}</td>
                                <td>
                                    {% if p.fecha_partido %}
                                    <div class="fw-bold text-white">{{ p.fecha_partido|date:"d/m/Y" }}</div>
                                    <small class="text-white-50 text-capitalize">{{ p.fecha_partido|date:"l" }}</small>
                                    {% else %}
                                    <span class="text-white-50 fst-italic small">Por programar</span>
                                    {% endif %}
                                </td>
                                <td class="text-center">
                                    {% if p.grupo %}
                                    <span class="badge badge-grupo-tag badge-grupo-{{ p.grupo.nombre_grupo }} badge-grupo-print-{{ p.grupo.nombre_grupo }}">
                                        Grupo {{ p.grupo.nombre_grupo }}
                                    </span>
                                    {% else %}
                                    <span class="badge bg-secondary text-white-50 small">General</span>
                                    {% endif %}
                                </td>
                                <td class="text-end fw-bold text-white">
                                    {{ p.equipo_local.nombre_equipo }}
                                    <i class="fas fa-shield-alt text-info ms-1"></i>
                                </td>
                                <td class="text-center">
                                    {% if p.jugado %}
                                    <span class="badge bg-success fs-6 fw-bold px-3 py-1 shadow-sm">
                                        {{ p.goles_local }} - {{ p.goles_visitante }}
                                    </span>
                                    {% else %}
                                    <span class="badge bg-dark border border-secondary text-white-50 px-2 py-1">
                                        vs
                                    </span>
                                    {% endif %}
                                </td>
                                <td class="fw-bold text-white">
                                    <i class="fas fa-shield-alt text-warning me-1"></i>
                                    {{ p.equipo_visitante.nombre_equipo }}
                                </td>
                                <td class="text-center">
                                    {% if p.jugado %}
                                    <span class="badge bg-primary text-white px-2 py-1 small">
                                        <i class="fas fa-check-circle me-1"></i>Jugado
                                    </span>
                                    {% else %}
                                    <span class="badge bg-secondary text-white-50 px-2 py-1 small">
                                        <i class="far fa-clock me-1"></i>Pendiente
                                    </span>
                                    {% endif %}
                                </td>
                            </tr>
                            {% empty %}
                            <tr>
                                <td colspan="7" class="text-center text-white-50 py-4">No hay partidos registrados en la fase de grupos.</td>
                            </tr>
                            {% endfor %}
                        </tbody>
                    </table>
                </div>
            </div>"""

if old_equipos_section in content:
    content = content.replace(old_equipos_section, new_equipos_and_cronograma_section, 1)
    template_path.write_text(content, encoding="utf-8")
    print("SUCCESS: Template actualizado correctamente con equipos y cronograma.")
else:
    # Intento con normalización de line endings si es necesario
    content_norm = content.replace("\r\n", "\n")
    old_norm = old_equipos_section.replace("\r\n", "\n")
    if old_norm in content_norm:
        content_norm = content_norm.replace(old_norm, new_equipos_and_cronograma_section.replace("\r\n", "\n"), 1)
        template_path.write_text(content_norm, encoding="utf-8")
        print("SUCCESS (norm): Template actualizado correctamente con equipos y cronograma.")
    else:
        print("ERROR: No se encontró old_equipos_section en el template.")
        sys.exit(1)
