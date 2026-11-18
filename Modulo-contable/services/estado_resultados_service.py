from services.consolidacion_service import consolidar_informacion_contable
from models.asiento import obtener_saldo_cuenta
from models.plan_cuentas import obtener_cuenta_por_codigo

# Códigos de cuentas contables para el Estado de Resultados
CUENTA_INGRESOS = '4105'       # Ventas (acreedora)
CUENTA_COSTO_VENTAS = '5105'   # Costo de ventas (deudora)
CUENTA_GASTO_NOMINA = '5205'   # Gastos de nómina (deudora)
CUENTA_GASTO_DEDUCIBLES = '5210'  # Gastos generales deducibles (deudora)
CUENTA_SERVICIOS = '5220'      # Servicios públicos (deudora)
CUENTA_ARRENDAMIENTOS = '5230' # Arriendos (deudora)


def _saldo_cuenta(codigo, fecha_inicio=None, fecha_fin=None):
    """Retorna el saldo (debe - haber) de una cuenta contable en el período."""
    cuenta = obtener_cuenta_por_codigo(codigo)
    if not cuenta:
        return 0.0
    saldo = obtener_saldo_cuenta(cuenta['id_cuenta'], fecha_inicio, fecha_fin)
    return round(saldo['saldo'], 2)


def _valor_ingreso(codigo, fecha_inicio=None, fecha_fin=None):
    """
    Para cuentas acreedoras (ingresos), el ingreso neto es haber - debe.
    obtener_saldo_cuenta retorna debe - haber, por lo que el ingreso es -saldo.
    """
    saldo = _saldo_cuenta(codigo, fecha_inicio, fecha_fin)
    # Si saldo es negativo (haber > debe), hay ingreso
    return round(abs(saldo) if saldo < 0 else 0.0, 2)


def _valor_gasto(codigo, fecha_inicio=None, fecha_fin=None):
    """
    Para cuentas deudoras (costos y gastos), el gasto neto es debe - haber.
    """
    saldo = _saldo_cuenta(codigo, fecha_inicio, fecha_fin)
    return round(saldo if saldo > 0 else 0.0, 2)


def generar_estado_resultados(fecha_inicio=None, fecha_fin=None):
    """
    CU-01: Genera el Estado de Resultados consolidado.

    Intenta calcular desde los asientos contables (doble entrada). Si no hay
    asientos registrados, cae al método antiguo de consolidación de tablas
    sueltas para mantener compatibilidad.
    """
    # --- Intento 1: Calcular desde asientos contables ---
    ingresos = _valor_ingreso(CUENTA_INGRESOS, fecha_inicio, fecha_fin)
    costo_ventas = _valor_gasto(CUENTA_COSTO_VENTAS, fecha_inicio, fecha_fin)
    gasto_nomina = _valor_gasto(CUENTA_GASTO_NOMINA, fecha_inicio, fecha_fin)
    gasto_deducibles = _valor_gasto(CUENTA_GASTO_DEDUCIBLES, fecha_inicio, fecha_fin)
    gasto_servicios = _valor_gasto(CUENTA_SERVICIOS, fecha_inicio, fecha_fin)
    gasto_arrendamientos = _valor_gasto(CUENTA_ARRENDAMIENTOS, fecha_inicio, fecha_fin)

    hay_asientos = any([
        ingresos > 0, costo_ventas > 0, gasto_nomina > 0,
        gasto_deducibles > 0, gasto_servicios > 0, gasto_arrendamientos > 0
    ])

    if hay_asientos:
        utilidad_bruta = round(ingresos - costo_ventas, 2)
        gastos_operativos = round(
            gasto_nomina + gasto_deducibles + gasto_servicios + gasto_arrendamientos, 2
        )
        utilidad_neta = round(utilidad_bruta - gastos_operativos, 2)

        return {
            'ingresos_totales': round(ingresos, 2),
            'costo_ventas': round(costo_ventas, 2),
            'utilidad_bruta': utilidad_bruta,
            'gastos_operativos': gastos_operativos,
            'desglose_gastos': {
                'nomina': round(gasto_nomina, 2),
                'gastos_deducibles': round(gasto_deducibles, 2),
                'perdidas_inventario': round(gasto_servicios + gasto_arrendamientos, 2),
            },
            'utilidad_neta': utilidad_neta
        }

    # --- Intento 2: Método antiguo (consolidación de tablas sueltas) ---
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
