"""Núcleo contable: comprobantes, libro mayor y balance de prueba.

Este módulo implementa la parte útil del libro NIIF/PYMES: un plan único de
cuentas, comprobantes balanceados de partida doble, libro mayor por cuenta y
balance de prueba. No intenta replicar los estados financieros completos del
libro; eso queda para una fase posterior sobre esta misma base.
"""

from datetime import date, datetime
from decimal import Decimal, ROUND_HALF_UP

from database.connection import obtener_conexion

CENTAVO = Decimal("0.01")
TIPOS_COMPROBANTE = ("DIARIO", "INGRESO", "EGRESO", "AJUSTE", "NOMINA", "CIERRE")
PREFIJOS = {
    "DIARIO": "DIA",
    "INGRESO": "ING",
    "EGRESO": "EGR",
    "AJUSTE": "AJU",
    "NOMINA": "NOM",
    "CIERRE": "CIE",
}


def _decimal(valor):
    """Convierte un valor de formulario/BD a Decimal sin lanzar excepciones."""
    if valor is None or valor == "":
        return Decimal("0")
    try:
        return Decimal(str(valor))
    except (TypeError, ValueError, ArithmeticError):
        return Decimal("0")


def _redondear(valor):
    return _decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _fecha(valor):
    """Normaliza una fecha ISO (YYYY-MM-DD) a ``date``."""
    if isinstance(valor, datetime):
        return valor.date()
    if isinstance(valor, date):
        return valor
    texto = (valor or "").strip()
    if not texto:
        raise ValueError("La fecha es obligatoria.")
    try:
        return datetime.strptime(texto[:10], "%Y-%m-%d").date()
    except ValueError as error:
        raise ValueError("La fecha debe tener el formato AAAA-MM-DD.") from error


def _serializar(fila):
    """Convierte Decimal/date/datetime a tipos que Flask pueda devolver."""
    salida = {}
    for clave, valor in fila.items():
        if isinstance(valor, Decimal):
            salida[clave] = float(valor)
        elif isinstance(valor, datetime):
            salida[clave] = valor.strftime("%Y-%m-%d %H:%M:%S")
        elif isinstance(valor, date):
            salida[clave] = valor.strftime("%Y-%m-%d")
        else:
            salida[clave] = valor
    return salida


# ---------------------------------------------------------------------------
# Plan único de cuentas
# ---------------------------------------------------------------------------

def buscar_cuentas(termino=None, solo_movimiento=True, limite=80):
    """Busca cuentas por código o nombre.

    ``solo_movimiento`` deja por fuera las cuentas de mayor que solo agrupan
    subcuentas, que no deberían usarse en un comprobante.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT id_cuenta, codigo, nombre, nivel, clase, grupo,
                       naturaleza, es_movimiento
                FROM puc_cuentas
                WHERE activo = 1
            """
            params = []
            if solo_movimiento:
                sql += " AND es_movimiento = 1"
            termino = (termino or "").strip()
            if termino:
                sql += " AND (codigo LIKE %s OR nombre LIKE %s)"
                patron = f"%{termino}%"
                params.extend([patron, patron])
            sql += " ORDER BY codigo LIMIT %s"
            params.append(max(1, min(int(limite or 80), 500)))
            cursor.execute(sql, params)
            return [_serializar(fila) for fila in cursor.fetchall()]
    finally:
        conexion.close()


def obtener_cuenta_por_codigo(codigo):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_cuenta, codigo, nombre, nivel, clase, grupo,
                       naturaleza, es_movimiento
                FROM puc_cuentas
                WHERE codigo = %s AND activo = 1
                """,
                (str(codigo).strip(),),
            )
            fila = cursor.fetchone()
            return _serializar(fila) if fila else None
    finally:
        conexion.close()


def crear_cuenta(codigo, nombre, naturaleza="DEBITO", grupo=None, clase=None):
    """Agrega una cuenta personalizada al PUC (por ejemplo, una cuenta nueva)."""
    codigo = str(codigo or "").strip()
    nombre = " ".join((nombre or "").split())
    if not codigo or not nombre:
        raise ValueError("El código y el nombre de la cuenta son obligatorios.")
    naturaleza = (naturaleza or "DEBITO").upper()
    if naturaleza not in ("DEBITO", "CREDITO"):
        raise ValueError("La naturaleza debe ser DEBITO o CREDITO.")

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_cuenta FROM puc_cuentas WHERE codigo = %s", (codigo,))
            if cursor.fetchone():
                raise ValueError("Ya existe una cuenta con ese código.")
            cursor.execute(
                """
                INSERT INTO puc_cuentas
                    (codigo, nombre, nivel, clase, grupo, naturaleza, es_movimiento)
                VALUES (%s, %s, %s, %s, %s, %s, 1)
                """,
                (
                    codigo,
                    nombre,
                    len(codigo),
                    (clase or codigo[:1])[:1],
                    grupo,
                    naturaleza,
                ),
            )
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()


# ---------------------------------------------------------------------------
# Comprobantes
# ---------------------------------------------------------------------------

def _siguiente_numero(cursor, tipo, fecha):
    prefijo = PREFIJOS.get(tipo, "COM")
    base = f"{prefijo}-{fecha.strftime('%Y%m')}-"
    cursor.execute(
        "SELECT numero FROM comprobantes WHERE numero LIKE %s ORDER BY numero DESC LIMIT 1",
        (f"{base}%",),
    )
    fila = cursor.fetchone()
    consecutivo = 1
    if fila:
        try:
            consecutivo = int(str(fila["numero"]).rsplit("-", 1)[1]) + 1
        except (ValueError, IndexError):
            consecutivo = 1
    for intento in range(1000):
        numero = f"{base}{consecutivo + intento:05d}"
        cursor.execute("SELECT 1 FROM comprobantes WHERE numero = %s", (numero,))
        if not cursor.fetchone():
            return numero
    raise ValueError("No se pudo generar un número de comprobante único.")


def _resolver_cuenta(cursor, linea):
    id_cuenta = linea.get("id_cuenta")
    codigo = (linea.get("codigo") or linea.get("codigo_cuenta") or "").strip()
    if id_cuenta:
        cursor.execute(
            """
            SELECT id_cuenta, codigo, nombre, es_movimiento
            FROM puc_cuentas WHERE id_cuenta = %s AND activo = 1
            """,
            (id_cuenta,),
        )
    elif codigo:
        cursor.execute(
            """
            SELECT id_cuenta, codigo, nombre, es_movimiento
            FROM puc_cuentas WHERE codigo = %s AND activo = 1
            """,
            (codigo,),
        )
    else:
        raise ValueError("Cada línea debe indicar una cuenta contable.")
    cuenta = cursor.fetchone()
    if not cuenta:
        raise ValueError(f"La cuenta {codigo or id_cuenta!r} no existe en el PUC.")
    if not cuenta["es_movimiento"]:
        raise ValueError(
            f"La cuenta {cuenta['codigo']} es de mayor y no admite movimientos. "
            "Selecciona una subcuenta."
        )
    return cuenta


def crear_comprobante(tipo, fecha, descripcion, lineas, id_usuario=None,
                      id_tercero=None, numero=None, origen="MANUAL",
                      id_origen=None, conexion=None):
    """Crea un comprobante balanceado y sus líneas.

    ``lineas`` es una lista de diccionarios con ``codigo`` (o ``id_cuenta``),
    ``debito``, ``credito``, y opcionalmente ``descripcion`` e ``id_tercero``.
    La función es transaccional: si una línea falla, no se guarda nada.
    """
    tipo = (tipo or "DIARIO").upper()
    if tipo not in TIPOS_COMPROBANTE:
        raise ValueError("Tipo de comprobante no válido.")
    fecha = _fecha(fecha)
    descripcion = " ".join((descripcion or "").split())
    if not descripcion:
        raise ValueError("La descripción del comprobante es obligatoria.")
    if not isinstance(lineas, list) or len(lineas) < 2:
        raise ValueError("Un comprobante necesita al menos dos líneas.")

    propia = conexion is None
    conexion = conexion or obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            preparadas = []
            total_debito = Decimal("0")
            total_credito = Decimal("0")

            for linea in lineas:
                debito = _redondear(linea.get("debito"))
                credito = _redondear(linea.get("credito"))
                if debito < 0 or credito < 0:
                    raise ValueError("Los débitos y créditos no pueden ser negativos.")
                if debito == 0 and credito == 0:
                    continue
                if debito > 0 and credito > 0:
                    raise ValueError("Una línea no puede tener débito y crédito al mismo tiempo.")
                cuenta = _resolver_cuenta(cursor, linea)
                tercero = linea.get("id_tercero") or id_tercero
                preparadas.append({
                    "id_cuenta": cuenta["id_cuenta"],
                    "id_tercero": tercero,
                    "descripcion": (linea.get("descripcion") or descripcion)[:255],
                    "debito": debito,
                    "credito": credito,
                })
                total_debito += debito
                total_credito += credito

            if len(preparadas) < 2:
                raise ValueError("El comprobante no tiene líneas con valor.")
            if abs(total_debito - total_credito) >= CENTAVO:
                raise ValueError(
                    "El comprobante no está balanceado: "
                    f"débitos {total_debito:.2f} y créditos {total_credito:.2f}."
                )

            numero = (numero or "").strip() or _siguiente_numero(cursor, tipo, fecha)
            cursor.execute(
                """
                INSERT INTO comprobantes
                    (numero, tipo, fecha, descripcion, id_tercero, id_usuario,
                     estado, origen, id_origen, total_debito, total_credito)
                VALUES (%s, %s, %s, %s, %s, %s, 'CONTABILIZADO', %s, %s, %s, %s)
                """,
                (
                    numero, tipo, fecha, descripcion, id_tercero, id_usuario,
                    origen, id_origen, total_debito, total_credito,
                ),
            )
            id_comprobante = cursor.lastrowid

            cursor.executemany(
                """
                INSERT INTO comprobante_detalle
                    (id_comprobante, id_cuenta, id_tercero, descripcion,
                     debito, credito)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                [
                    (
                        id_comprobante, fila["id_cuenta"], fila["id_tercero"],
                        fila["descripcion"], fila["debito"], fila["credito"],
                    )
                    for fila in preparadas
                ],
            )
            if propia:
                conexion.commit()
            return {
                "id_comprobante": id_comprobante,
                "numero": numero,
                "total_debito": float(total_debito),
                "total_credito": float(total_credito),
            }
    except Exception:
        if propia:
            conexion.rollback()
        raise
    finally:
        if propia:
            conexion.close()


def listar_comprobantes(fecha_inicio=None, fecha_fin=None, estado=None,
                        tipo=None, limite=200):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT c.id_comprobante, c.numero, c.tipo, c.fecha, c.descripcion,
                       c.estado, c.origen, c.total_debito, c.total_credito,
                       u.nombre AS usuario, t.nombre AS tercero
                FROM comprobantes c
                LEFT JOIN usuarios u ON u.id_usuario = c.id_usuario
                LEFT JOIN terceros t ON t.id_tercero = c.id_tercero
                WHERE 1 = 1
            """
            params = []
            if fecha_inicio:
                sql += " AND c.fecha >= %s"
                params.append(_fecha(fecha_inicio))
            if fecha_fin:
                sql += " AND c.fecha <= %s"
                params.append(_fecha(fecha_fin))
            if estado:
                sql += " AND c.estado = %s"
                params.append(estado.upper())
            if tipo:
                sql += " AND c.tipo = %s"
                params.append(tipo.upper())
            sql += " ORDER BY c.fecha DESC, c.id_comprobante DESC LIMIT %s"
            params.append(max(1, min(int(limite or 200), 1000)))
            cursor.execute(sql, params)
            return [_serializar(fila) for fila in cursor.fetchall()]
    finally:
        conexion.close()


def obtener_comprobante(id_comprobante):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT c.id_comprobante, c.numero, c.tipo, c.fecha, c.descripcion,
                       c.estado, c.origen, c.total_debito, c.total_credito,
                       u.nombre AS usuario, t.nombre AS tercero
                FROM comprobantes c
                LEFT JOIN usuarios u ON u.id_usuario = c.id_usuario
                LEFT JOIN terceros t ON t.id_tercero = c.id_tercero
                WHERE c.id_comprobante = %s
                """,
                (id_comprobante,),
            )
            comprobante = cursor.fetchone()
            if not comprobante:
                return None
            cursor.execute(
                """
                SELECT d.id_detalle, d.descripcion, d.debito, d.credito,
                       c.codigo, c.nombre AS cuenta, c.naturaleza,
                       t.nombre AS tercero
                FROM comprobante_detalle d
                JOIN puc_cuentas c ON c.id_cuenta = d.id_cuenta
                LEFT JOIN terceros t ON t.id_tercero = d.id_tercero
                WHERE d.id_comprobante = %s
                ORDER BY d.id_detalle
                """,
                (id_comprobante,),
            )
            resultado = _serializar(comprobante)
            resultado["detalle"] = [_serializar(fila) for fila in cursor.fetchall()]
            return resultado
    finally:
        conexion.close()


def anular_comprobante(id_comprobante):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT estado, origen, id_origen FROM comprobantes WHERE id_comprobante = %s",
                (id_comprobante,),
            )
            fila = cursor.fetchone()
            if not fila:
                raise ValueError("Comprobante no encontrado.")
            if fila["estado"] == "ANULADO":
                raise ValueError("El comprobante ya está anulado.")
            cursor.execute(
                "UPDATE comprobantes SET estado = 'ANULADO' WHERE id_comprobante = %s",
                (id_comprobante,),
            )
            afectados = cursor.rowcount
            # Si era el comprobante de un periodo de nómina, el periodo vuelve
            # a estado calculado para que pueda revisarse y contabilizarse de nuevo.
            if fila["origen"] == "NOMINA" and fila["id_origen"]:
                cursor.execute(
                    """
                    UPDATE nomina_periodos
                    SET estado = 'CALCULADO', id_comprobante = NULL
                    WHERE id_periodo = %s
                    """,
                    (fila["id_origen"],),
                )
            conexion.commit()
            return afectados
    finally:
        conexion.close()


# ---------------------------------------------------------------------------
# Libro mayor, auxiliar y balance de prueba
# ---------------------------------------------------------------------------

def libro_mayor(cuenta_codigo, fecha_inicio=None, fecha_fin=None, id_tercero=None):
    """Movimientos de una cuenta con saldo corrido.

    Si la cuenta es de mayor (no es de movimiento), se incluyen sus
    subcuentas por prefijo.
    """
    cuenta_codigo = str(cuenta_codigo or "").strip()
    if not cuenta_codigo:
        raise ValueError("Selecciona una cuenta contable.")

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT codigo, nombre, es_movimiento, naturaleza
                FROM puc_cuentas WHERE codigo = %s AND activo = 1
                """,
                (cuenta_codigo,),
            )
            cuenta = cursor.fetchone()
            if not cuenta:
                raise ValueError("La cuenta indicada no existe en el PUC.")

            filtro_cuenta = "c.codigo = %s"
            params = [cuenta_codigo]
            if not cuenta["es_movimiento"]:
                filtro_cuenta = "c.codigo LIKE %s"
                params = [f"{cuenta_codigo}%"]

            sql = f"""
                SELECT co.id_comprobante, co.numero, co.fecha, co.tipo,
                       co.descripcion AS comprobante, d.descripcion,
                       d.debito, d.credito, c.codigo, c.nombre AS cuenta,
                       t.nombre AS tercero
                FROM comprobante_detalle d
                JOIN comprobantes co ON co.id_comprobante = d.id_comprobante
                JOIN puc_cuentas c ON c.id_cuenta = d.id_cuenta
                LEFT JOIN terceros t ON t.id_tercero = d.id_tercero
                WHERE co.estado <> 'ANULADO' AND {filtro_cuenta}
            """
            if fecha_inicio:
                sql += " AND co.fecha >= %s"
                params.append(_fecha(fecha_inicio))
            if fecha_fin:
                sql += " AND co.fecha <= %s"
                params.append(_fecha(fecha_fin))
            if id_tercero:
                sql += " AND d.id_tercero = %s"
                params.append(id_tercero)
            sql += " ORDER BY co.fecha, co.id_comprobante, d.id_detalle"

            cursor.execute(sql, params)
            filas = cursor.fetchall()

            saldo = Decimal("0")
            movimientos = []
            for fila in filas:
                saldo += _decimal(fila["debito"]) - _decimal(fila["credito"])
                item = _serializar(fila)
                item["saldo"] = float(saldo)
                movimientos.append(item)

            return {
                "cuenta": _serializar(cuenta),
                "movimientos": movimientos,
                "total_debito": float(sum(_decimal(f["debito"]) for f in filas)),
                "total_credito": float(sum(_decimal(f["credito"]) for f in filas)),
                "saldo_final": float(saldo),
            }
    finally:
        conexion.close()


def balance_prueba(fecha_inicio=None, fecha_fin=None):
    """Balance de prueba por cuenta con sumas iguales."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT c.codigo, c.nombre, c.clase, c.naturaleza,
                       COALESCE(SUM(d.debito), 0) AS debitos,
                       COALESCE(SUM(d.credito), 0) AS creditos
                FROM comprobante_detalle d
                JOIN comprobantes co ON co.id_comprobante = d.id_comprobante
                JOIN puc_cuentas c ON c.id_cuenta = d.id_cuenta
                WHERE co.estado <> 'ANULADO'
            """
            params = []
            if fecha_inicio:
                sql += " AND co.fecha >= %s"
                params.append(_fecha(fecha_inicio))
            if fecha_fin:
                sql += " AND co.fecha <= %s"
                params.append(_fecha(fecha_fin))
            sql += """
                GROUP BY c.codigo, c.nombre, c.clase, c.naturaleza
                ORDER BY c.codigo
            """
            cursor.execute(sql, params)
            filas = cursor.fetchall()

            cuentas = []
            total_debitos = Decimal("0")
            total_creditos = Decimal("0")
            for fila in filas:
                debitos = _decimal(fila["debitos"])
                creditos = _decimal(fila["creditos"])
                if debitos == 0 and creditos == 0:
                    continue
                total_debitos += debitos
                total_creditos += creditos
                item = _serializar(fila)
                item["saldo"] = float(debitos - creditos)
                # El saldo se presenta en la columna que corresponde al movimiento.
                item["saldo_debito"] = float(max(debitos - creditos, Decimal("0")))
                item["saldo_credito"] = float(max(creditos - debitos, Decimal("0")))
                cuentas.append(item)

            return {
                "cuentas": cuentas,
                "total_debitos": float(total_debitos),
                "total_creditos": float(total_creditos),
                "diferencia": float(total_debitos - total_creditos),
                "cuadra": abs(total_debitos - total_creditos) < CENTAVO,
            }
    finally:
        conexion.close()


def resumen_cuentas_por_clase(fecha_inicio=None, fecha_fin=None):
    """Totales de débito/crédito agrupados por la clase del PUC (1..9)."""
    balance = balance_prueba(fecha_inicio, fecha_fin)
    resumen = {}
    for cuenta in balance["cuentas"]:
        clase = cuenta["clase"]
        fila = resumen.setdefault(clase, {"clase": clase, "debitos": 0.0, "creditos": 0.0})
        fila["debitos"] += cuenta["debitos"]
        fila["creditos"] += cuenta["creditos"]
    return [resumen[clave] for clave in sorted(resumen)]
