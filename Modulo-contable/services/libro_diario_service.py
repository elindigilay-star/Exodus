"""Servicio del Libro Diario contable.

Genera el listado cronológico de todos los asientos contables contabilizados
o en borrador, con sus movimientos debe/haber, filtrado por período.
"""

from datetime import datetime, date

from models.asiento import listar_asientos, obtener_asiento


def _formatear_fecha(valor):
    """Convierte datetime/date/string a formato 'YYYY-MM-DD HH:MM:SS' o 'YYYY-MM-DD'."""
    if valor is None:
        return None
    if isinstance(valor, (datetime, date)):
        return valor.strftime('%Y-%m-%d %H:%M:%S')
    return str(valor)


def generar_libro_diario(fecha_inicio=None, fecha_fin=None, estado=None):
    """
    Retorna los asientos del libro diaro con sus movimientos.

    Cada asiento incluye:
      - datos del asiento (numero, fecha, descripcion, referencia, estado, usuario)
      - lista de movimientos (cuenta, debe, haber, detalle, iva)
    """
    asientos = listar_asientos(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=estado,
    )

    resultado = []
    for asiento in asientos:
        asiento_completo = obtener_asiento(asiento["id_asiento"])
        if asiento_completo:
            # Preservar totales calculados en el listado (convertir a float)
            asiento_completo['total_debe'] = float(asiento.get('total_debe', 0) or 0)
            asiento_completo['total_haber'] = float(asiento.get('total_haber', 0) or 0)
            # Normalizar fechas a string para serialización JSON
            asiento_completo['fecha'] = _formatear_fecha(asiento_completo.get('fecha'))
            asiento_completo['fecha_creacion'] = _formatear_fecha(asiento_completo.get('fecha_creacion'))
            asiento_completo['fecha_contabilizacion'] = _formatear_fecha(asiento_completo.get('fecha_contabilizacion'))
            resultado.append(asiento_completo)

    return resultado


def generar_libro_diario_resumido(fecha_inicio=None, fecha_fin=None, estado=None):
    """
    Retorna una versión resumida del libro diaro (sin detalle de movimientos)
    para mostrar en tabla principal.
    """
    return listar_asientos(
        fecha_inicio=fecha_inicio,
        fecha_fin=fecha_fin,
        estado=estado,
    )