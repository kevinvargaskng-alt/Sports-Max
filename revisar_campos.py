import os
import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")
django.setup()

from django.apps import apps

tablas_objetivo = {
    "interfichas_torneointerfichas": ["public_id"],
    "interfichas_equipointerfichas": ["foto_equipo", "public_id"],
    "interfichas_partidointerfichas": ["public_id"],
    "interfichas_resultadotorneo": ["public_id"],
    "gimnasio_reserva": ["public_id"],
    "gimnasio_gimnasioconfig": ["public_id"],
    "gimnasio_maquina": ["fecha_adquisicion", "public_id"],
    "inventario_elementodeportivo": ["categoria", "public_id", "ubicacion"],
    "inventario_reserva": ["public_id"],
    "inventario_prestamo": ["fecha_vencimiento", "public_id"],
    "inventario_detalleprestamo": ["public_id"],
    "inventario_devolucion": ["public_id"],
    "inventario_sancion": ["public_id"],
    "usuarios_sugerencia": ["public_id"],
    "habitos_saludables_habeasdataconsent": ["public_id"],
    "habitos_saludables_habitosaludable": ["public_id"],
    "habitos_saludables_rutinafisica": ["public_id"],
    "habitos_saludables_piramidenutricional": ["public_id"],
    "habitos_saludables_materialapoyo": ["public_id"],
    "habitos_saludables_seguimientosalud": ["public_id"],
}

for modelo in apps.get_models():
    tabla = modelo._meta.db_table

    if tabla not in tablas_objetivo:
        continue

    print("\n" + "=" * 70)
    print("MODELO:", modelo.__name__)
    print("TABLA:", tabla)

    for campo in modelo._meta.local_fields:
        if campo.column in tablas_objetivo[tabla]:
            print("\nCAMPO:", campo.name)
            print("COLUMNA:", campo.column)
            print("TIPO:", campo.__class__.__name__)
            print("DB TYPE:", campo.db_type(django.db.connection))
            print("NULL:", campo.null)
            print("BLANK:", campo.blank)
            print("DEFAULT:", campo.default)
            print("EDITABLE:", campo.editable)

print("\n" + "=" * 70)
print("FIN")
print("=" * 70)