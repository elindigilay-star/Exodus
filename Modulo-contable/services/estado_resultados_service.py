from services.consolidacion_service import consolidar_informacion_contable

def generar_estado_resultados(fecha_inicio=None, fecha_fin=None):
    """
    CU-01: Genera el Estado de Resultados consolidado.
    """
    datos = consolidar_informacion_contable(fecha_inicio, fecha_fin)

    # Validar si no hay ningún registro en el sistema
    if (datos['ingresos_totales'] == 0 and
            datos['costo_ventas'] == 0 and
            datos['costo_nomina'] == 0 and
        datos['gastos_deducibles'] == 0 and
        datos['compras_inventario'] == 0 and
        datos['perdidas_inventario'] == 0):
        raise ValueError(
            "No existen datos suficientes registrados en inventario, nómina o "
            "gastos para generar el Estado de Resultados."
        )

    # Cálculos Financieros
    ingresos_totales = datos['ingresos_totales']
    costo_ventas = datos['costo_ventas']
    utilidad_bruta = ingresos_totales - costo_ventas

    # Mermas, salidas y ajustes negativos de inventario son un gasto del periodo.
    perdidas = datos['perdidas_inventario']
    gastos_operativos = datos['costo_nomina'] + datos['gastos_deducibles'] + perdidas
    utilidad_neta = utilidad_bruta - gastos_operativos

    return {
        'ingresos_totales': ingresos_totales,
        'costo_ventas': costo_ventas,
        'utilidad_bruta': utilidad_bruta,
        'gastos_operativos': gastos_operativos,
        'desglose_gastos': {
            'nomina': datos['costo_nomina'],
            'gastos_deducibles': datos['gastos_deducibles'],
            'perdidas_inventario': perdidas
        },
        'utilidad_neta': utilidad_neta
    }
