"""Servicio del Libro Mayor contable.

Genera el estado de cuenta de cada cuenta contable con sus movimientos,
saldo acumulado y balance deudor/acreedor por período.
"""

from models.asiento import obtener_saldo_cuenta
from models.plan_cuentas import listar_cuentas


def generar_libro_mayor(fecha_inicio=None, fecha_fin=None, id_cuenta=None):
    """
    Retorna el libro mayor: lista de cuentas con sus saldos en el período.

    Cada entrada incluye:
      - datos de la cuenta (codigo, nombre, naturaleza, nivel)
      - saldo: total_debe, total_haber, saldo (debe - haber)
    """
    cuentas = listar_cuentas(activo=1, solo_movimiento=True)

    resultado = []
    for cuenta in cuentas:
        if id_cuenta and cuenta["id_cuenta"] != id_cuenta:
            continue

        saldo = obtener_saldo_cuenta(
            cuenta["id_cuenta"],
            fecha_inicio=fecha_inicio,
            fecha_fin=fecha_fin,
        )

        # Solo incluir cuentas que tengan movimiento en el período
        if saldo["total_debe"] == 0 and saldo["total_haber"] == 0:
            continue

        resultado.append({
            "id_cuenta": cuenta["id_cuenta"],
            "codigo": cuenta["codigo"],
            "nombre": cuenta["nombre"],
            "naturaleza": cuenta["naturaleza"],
            "nivel": cuenta["nivel"],
            "total_debe": round(saldo["total_debe"], 2),
            "total_haber": round(saldo["total_haber"], 2),
            "saldo": round(saldo["saldo"], 2),
        })

    # Ordenar por código contable
    resultado.sort(key=lambda c: c["codigo"])
    return resultado


def obtener_movimientos_cuenta(id_cuenta, fecha_inicio=None, fecha_fin=None):
    """
    Retorna los movimientos contables detallados de una cuenta específica
    en el período dado (para ver el detalle del libro mayor de una cuenta).
    """
    from database.connection import obtener_conexion

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT m.id_movimiento, m.id_asiento, a.numero_asiento, a.fecha,
                       a.descripcion AS asiento_descripcion,
                       m.debe, m.haber, m.detalle,
                       m.base_gravable, m.valor_iva, m.tipo_iva,
                       a.estado
                FROM movimientos_contables m
                JOIN asientos_contables a ON a.id_asiento = m.id_asiento
                WHERE m.id_cuenta = %s AND a.estado = 'CONTABLE'
            """
            params = [id_cuenta]
            if fecha_inicio and fecha_fin:
                sql += " AND a.fecha BETWEEN %s AND %s"
                params.extend([fecha_inicio, fecha_fin])
            sql += " ORDER BY a.fecha, a.numero_asiento, m.id_movimiento"

            cursor.execute(sql, params)
            movimientos = cursor.fetchall()

            # Calcular saldo acumulado
            saldo_acumulado = 0.0
            for mov in movimientos:
                debe = float(mov["debe"] or 0)
                haber = float(mov["haber"] or 0)
                saldo_acumulado += debe - haber
                mov["saldo_acumulado"] = round(saldo_acumulado, 2)
                mov["fecha"] = mov["fecha"].strftime("%Y-%m-%d %H:%M:%S") if mov["fecha"] else None

            return movimientos
    finally:
        conexion.close()