"""Servicio del Balance de Comprobación (prueba de saldos).

Valida que la suma total de saldos deudores sea igual a la suma total de
saldos acreedores al cierre de un período.
"""

from models.asiento import obtener_saldo_cuenta
from models.plan_cuentas import listar_cuentas


def generar_balance_comprobacion(fecha_inicio=None, fecha_fin=None):
    """
    Retorna el balance de comprobación por agrupación de naturaleza.

    Estructura:
      - cuentas: lista de cuentas con saldo deudor/acreedor
      - totales: total_deudor, total_acreedor, diferencia (debe ser 0)
      - cuadrado: booleano indicando si el balance está cuadrado
    """
    cuentas = listar_cuentas(activo=1, solo_movimiento=True)

    filas = []
    total_deudor = 0.0
    total_acreedor = 0.0

    for cuenta in cuentas:
        saldo = obtener_saldo_cuenta(
            cuenta["id_cuenta"],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        saldo_valor = round(saldo["saldo"], 2)
        if saldo_valor == 0:
            continue

        # Según la naturaleza de la cuenta, el saldo se clasifica
        if cuenta["naturaleza"] == "deudora":
            saldo_deudor = saldo_valor if saldo_valor > 0 else 0.0
            saldo_acreedor = abs(saldo_valor) if saldo_valor < 0 else 0.0
        elif cuenta["naturaleza"] == "acreedora":
            saldo_acreedor = abs(saldo_valor) if saldo_valor < 0 else 0.0
            saldo_deudor = saldo_valor if saldo_valor > 0 else 0.0
        else:
            # Naturaleza 'ninguna' (grupos): usar valor absoluto
            saldo_deudor = saldo_valor if saldo_valor > 0 else 0.0
            saldo_acreedor = abs(saldo_valor) if saldo_valor < 0 else 0.0

        total_deudor += saldo_deudor
        total_acreedor += saldo_acreedor

        filas.append({
            "id_cuenta": cuenta["id_cuenta"],
            "codigo": cuenta["codigo"],
            "nombre": cuenta["nombre"],
            "naturaleza": cuenta["naturaleza"],
            "saldo_deudor": round(saldo_deudor, 2),
            "saldo_acreedor": round(saldo_acreedor, 2),
        })

    diferencia = round(total_deudor - total_acreedor, 2)
    cuadrado = abs(diferencia) < 0.01

    filas.sort(key=lambda f: f["codigo"])

    return {
        "cuentas": filas,
        "totales": {
            "total_deudor": round(total_deudor, 2),
            "total_acreedor": round(total_acreedor, 2),
            "diferencia": diferencia,
        },
        "cuadrado": cuadrado,
        "fecha_inicio": fecha_inicio,
        "fecha_fin": fecha_fin,
    }