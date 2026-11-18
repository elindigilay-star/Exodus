from services.estado_resultados_service import generar_estado_resultados
from models.asiento import obtener_saldo_cuenta
from models.plan_cuentas import obtener_cuenta_por_codigo

# Códigos de cuentas contables para el Balance General
CUENTA_CAJA = '1105'         # Caja (deudora)
CUENTA_BANCOS = '1110'       # Bancos (deudora)
CUENTA_INVENTARIO = '1130'   # Inventario de mercancías (deudora)
CUENTA_PROVEEDORES = '2105'  # Proveedores / Cuentas por pagar (acreedora)
CUENTA_IVA_PAGAR = '2110'    # IVA por pagar (acreedora)
CUENTA_NOMINA_PAGAR = '2405' # Nómina por pagar (acreedora)
CUENTA_RETENCIONES = '2410'  # Retenciones y aportes por pagar (acreedora)
CUENTA_CAPITAL = '3105'      # Capital social (acreedora)
CUENTA_UTILIDADES = '3110'   # Utilidades acumuladas (acreedora)


def _saldo_cuenta(codigo, fecha_inicio=None, fecha_fin=None):
    """Retorna el saldo (debe - haber) de una cuenta contable en el período."""
    cuenta = obtener_cuenta_por_codigo(codigo)
    if not cuenta:
        return 0.0
    saldo = obtener_saldo_cuenta(cuenta['id_cuenta'], fecha_inicio, fecha_fin)
    return round(saldo['saldo'], 2)


def _valor_activo(codigo, fecha_inicio=None, fecha_fin=None):
    """
    Para cuentas deudora (activos), el saldo es debe - haber.
    """
    saldo = _saldo_cuenta(codigo, fecha_inicio, fecha_fin)
    return round(saldo if saldo > 0 else 0.0, 2)


def _valor_pasivo(codigo, fecha_inicio=None, fecha_fin=None):
    """
    Para cuentas acreedoras (pasivos y patrimonio), el saldo neto es haber - debe.
    obtener_saldo_cuenta retorna debe - haber, por lo que el pasivo es -saldo.
    """
    saldo = _saldo_cuenta(codigo, fecha_inicio, fecha_fin)
    return round(abs(saldo) if saldo < 0 else 0.0, 2)


def calcular_balance_general(fecha_inicio=None, fecha_fin=None):
    """
    CU-04: Calcula las partidas del Balance General.

    Calcula activos, pasivos y patrimonio a partir de los saldos de las
    cuentas contables (doble entrada). Si no hay asientos, cae al método
    antiguo de consolidación para mantener compatibilidad.
    """
    hay_asientos = False

    # Intentar obtener saldos desde asientos contables
    caja = _valor_activo(CUENTA_CAJA, fecha_inicio, fecha_fin)
    bancos = _valor_activo(CUENTA_BANCOS, fecha_inicio, fecha_fin)
    inventario = _valor_activo(CUENTA_INVENTARIO, fecha_inicio, fecha_fin)
    proveedores = _valor_pasivo(CUENTA_PROVEEDORES, fecha_inicio, fecha_fin)
    iva_pagar = _valor_pasivo(CUENTA_IVA_PAGAR, fecha_inicio, fecha_fin)
    nomina_pagar = _valor_pasivo(CUENTA_NOMINA_PAGAR, fecha_inicio, fecha_fin)
    retenciones = _valor_pasivo(CUENTA_RETENCIONES, fecha_inicio, fecha_fin)
    capital = _valor_pasivo(CUENTA_CAPITAL, fecha_inicio, fecha_fin)
    utilidades_acumuladas = _valor_pasivo(CUENTA_UTILIDADES, fecha_inicio, fecha_fin)

    hay_asientos = any([
        caja > 0, bancos > 0, inventario > 0,
        proveedores > 0, iva_pagar > 0, nomina_pagar > 0,
        retenciones > 0, capital > 0, utilidades_acumuladas > 0
    ])

    if hay_asientos:
        # --- Cálculo desde asientos contables ---
        efectivo_caja = round(caja + bancos, 2)
        total_activos = round(efectivo_caja + inventario, 2)

        pasivos_laborales = round(nomina_pagar + retenciones, 2)
        total_pasivos = round(proveedores + iva_pagar + pasivos_laborales, 2)

        # Patrimonio = Activos - Pasivos (ecuación contable)
        # También podemos mostrar capital + utilidades acumuladas + utilidad ejercicio
        total_patrimonio = round(total_activos - total_pasivos, 2)

        # Obtener utilidad del ejercicio desde el estado de resultados
        try:
            estado_res = generar_estado_resultados(fecha_inicio, fecha_fin)
            utilidad_ejercicio = estado_res['utilidad_neta']
        except ValueError:
            utilidad_ejercicio = 0.0

        return {
            'activos': {
                'efectivo_caja': efectivo_caja,
                'inventario': inventario,
                'total_activos': total_activos
            },
            'pasivos': {
                'pasivos_laborales': pasivos_laborales,
                'total_pasivos': total_pasivos
            },
            'patrimonio': {
                'utilidad_ejercicio': round(utilidad_ejercicio, 2),
                'total_patrimonio': total_patrimonio
            }
        }

    # --- Método antiguo (consolidación de tablas sueltas) ---
    try:
        estado_res = generar_estado_resultados(fecha_inicio, fecha_fin)
    except ValueError as error:
        raise ValueError(
            "No existen datos contables suficientes para calcular el Balance General."
        ) from error

    consolidado = consolidar_informacion_contable(fecha_inicio, fecha_fin)

    # 1. Activos
    cambio_inventario = consolidado['valor_inventario'] - consolidado['valor_inventario_inicial']
    desglose = estado_res['desglose_gastos']
    gastos_en_efectivo = desglose['nomina'] + desglose['gastos_deducibles']
    efectivo_caja = estado_res['ingresos_totales'] - cambio_inventario - gastos_en_efectivo
    inventario = consolidado['valor_inventario']
    total_activos = efectivo_caja + inventario

    # 2. Pasivos
    pasivos_laborales = consolidado.get('deducciones_nomina', 0.0) or 0.0
    total_pasivos = pasivos_laborales

    # 3. Patrimonio (Activo - Pasivo)
    patrimonio = total_activos - total_pasivos

    return {
        'activos': {
            'efectivo_caja': efectivo_caja,
            'inventario': inventario,
            'total_activos': total_activos
        },
        'pasivos': {
            'pasivos_laborales': pasivos_laborales,
            'total_pasivos': total_pasivos
        },
        'patrimonio': {
            'utilidad_ejercicio': estado_res['utilidad_neta'],
            'total_patrimonio': patrimonio
        }
    }
