from inventario.resumen import obtener_resumen_inventario, obtener_posicion_inventario
from nomina.modelo import obtener_resumen_nomina
from models.contabilidad import obtener_total_gastos

def consolidar_informacion_contable(fecha_inicio=None, fecha_fin=None):
    """
    CU-03: Consolida la información de inventario, nómina y gastos.
    Continúa con datos en 0.0 si alguno de los módulos no tiene registros.
    """
    # 1. Obtener inventario (Tolerante a fallos/vacíos)
    try:
        inventario = obtener_resumen_inventario(fecha_inicio, fecha_fin)
    except Exception:
        inventario = {'ingresos_totales': 0.0, 'costo_ventas': 0.0, 'compras': 0.0,
                      'costo_ventas_manuales': 0.0, 'perdidas': 0.0}

    try:
        valor_inventario = obtener_posicion_inventario()['valor_inventario']
    except Exception:
        valor_inventario = 0.0

    # 2. Obtener nómina (Tolerante a fallos/vacíos)
    try:
        nomina = obtener_resumen_nomina(fecha_inicio, fecha_fin)
    except Exception:
        nomina = {'costo_nomina': 0.0, 'deducciones': 0.0}

    # 3. Obtener gastos deducibles (Tolerante a fallos/vacíos)
    try:
        gastos = obtener_total_gastos(fecha_inicio, fecha_fin)
    except Exception:
        gastos = 0.0

    # 4. Unificar y retornar datos consolidados
    return {
        'ingresos_totales': inventario['ingresos_totales'],
        'costo_ventas': inventario['costo_ventas'],
        'costo_nomina': nomina['costo_nomina'],
        'deducciones_nomina': nomina['deducciones'],
        'gastos_deducibles': gastos,
        'compras_inventario': inventario['compras'],
        'costo_ventas_sin_stock': inventario['costo_ventas_manuales'],
        'perdidas_inventario': inventario['perdidas'],
        'valor_inventario': valor_inventario
    }