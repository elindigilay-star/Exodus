from services.consolidacion_service import consolidar_informacion_contable
from services.estado_resultados_service import generar_estado_resultados


def calcular_balance_general(fecha_inicio=None, fecha_fin=None):
    """CU-04: Calcula las partidas del Balance General.

    El inventario se refleja así:
      - Cambio en inventario (valor final - valor inicial) afecta al efectivo.
      - La mercancía que queda en bodega es un activo (a costo promedio).
    """
    try:
        estado_res = generar_estado_resultados(fecha_inicio, fecha_fin)
    except ValueError:
        raise ValueError("No existen datos contables suficientes para calcular el Balance General.")

    consolidado = consolidar_informacion_contable(fecha_inicio, fecha_fin)

    # 1. Activos
    # Cambio en inventario = valor actual - valor inicial
    # Si hay más inventario al final que al principio, significa que se compró mercancía con cash
    cambio_inventario = consolidado['valor_inventario'] - consolidado['valor_inventario_inicial']
    gastos_en_efectivo = estado_res['desglose_gastos']['nomina'] + estado_res['desglose_gastos']['gastos_deducibles']
    efectivo_caja = estado_res['ingresos_totales'] - cambio_inventario - gastos_en_efectivo
    inventario = consolidado['valor_inventario']
    total_activos = efectivo_caja + inventario

    # 2. Pasivos (Pasivos laborales por retenciones pendientes)
    pasivos = 0.0

    # 3. Patrimonio
    patrimonio = total_activos - pasivos

    return {
        'activos': {
            'efectivo_caja': efectivo_caja,
            'inventario': inventario,
            'total_activos': total_activos
        },
        'pasivos': {
            'pasivos_laborales': pasivos,
            'total_pasivos': pasivos
        },
        'patrimonio': {
            'utilidad_ejercicio': estado_res['utilidad_neta'],
            'total_patrimonio': patrimonio
        }
    }