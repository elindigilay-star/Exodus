"""Motor de liquidación de nómina de EXODUS Contable.

Toma la estructura útil del libro de liquidación: datos del trabajador,
horas extras y recargos, IBC, deducciones, retención en la fuente, aportes
patronales, provisiones, colilla y asiento contable. Los valores legales
viven en la tabla ``parametros_nomina`` y son editables desde la interfaz.
"""

from datetime import date, datetime, timedelta
from decimal import Decimal, ROUND_HALF_UP

from database.connection import obtener_conexion

CENTAVO = Decimal("0.01")
DIA = Decimal("1")

# Factores de horas extras/recargos tomados del libro de trabajo.
FACTORES_HORAS = {
    "HED": "HED_FACTOR",
    "HEN": "HEN_FACTOR",
    "RNOCT": "RNOCT_FACTOR",
    "HODF": "HODF_FACTOR",
    "HEDF": "HEDF_FACTOR",
    "HONDF": "HONDF_FACTOR",
    "HENDF": "HENDF_FACTOR",
}
CODIGOS_HORAS = set(FACTORES_HORAS)

# Conceptos que el motor calcula solo; no deben registrarse como novedades
# manuales para evitar duplicar salario, auxilio o aportes.
CONCEPTOS_AUTOMATICOS = {
    "SALARIO", "AUX_TRANSPORTE", "SALUD_EMPLEADO", "PENSION_EMPLEADO", "FSP",
}

# Parámetros iniciales. Se usan si la tabla está vacía o si falta una clave.
PARAMETROS_DEFECTO = {
    "SMMLV": 1750905.0,
    "AUXILIO_TRANSPORTE": 249095.0,
    "UVT": 52374.0,
    "HORAS_MES": 210.0,
    "SALUD_EMPLEADO": 4.0,
    "PENSION_EMPLEADO": 4.0,
    "SALUD_EMPLEADOR": 8.5,
    "PENSION_EMPLEADOR": 12.0,
    "SENA": 2.0,
    "ICBF": 3.0,
    "CAJA_COMPENSACION": 4.0,
    "PRIMA": 8.33,
    "CESANTIAS": 8.33,
    "INTERESES_CESANTIAS": 1.0,
    "VACACIONES": 4.17,
    "ARL_NIVEL_1": 0.522,
    "ARL_NIVEL_2": 1.044,
    "ARL_NIVEL_3": 2.436,
    "ARL_NIVEL_4": 4.35,
    "ARL_NIVEL_5": 6.96,
    "TOPE_AUXILIO_TRANSPORTE_SMMLV": 2.0,
    "TOPE_EXONERACION_SMMLV": 10.0,
    "TOPE_IBC_SMMLV": 25.0,
    "FSP_UMBRAL_1_SMMLV": 4.0,
    "FSP_UMBRAL_2_SMMLV": 16.0,
    "FSP_UMBRAL_3_SMMLV": 17.0,
    "FSP_UMBRAL_4_SMMLV": 20.0,
    "FSP_TASA_1": 1.0,
    "FSP_TASA_2": 1.2,
    "FSP_TASA_3": 1.4,
    "FSP_TASA_4": 1.6,
    "HED_FACTOR": 1.25,
    "HEN_FACTOR": 1.75,
    "RNOCT_FACTOR": 0.35,
    "HODF_FACTOR": 1.9,
    "HEDF_FACTOR": 2.15,
    "HONDF_FACTOR": 2.25,
    "HENDF_FACTOR": 2.65,
    "RETEFUENTE_EXENTO": 25.0,
    "RETEFUENTE_TOPE_EXENTO_UVT_MES": 65.8333,
    "RETEFUENTE_DEPENDIENTES": 10.0,
    "RETEFUENTE_DEPENDIENTES_TOPE_UVT_MES": 32.0,
    "RETEFUENTE_DEPENDIENTES_UVT_MES": 6.0,
    "RETEFUENTE_PREPAGADA_TOPE_UVT_MES": 16.0,
    "RETEFUENTE_INTERESES_TOPE_UVT_MES": 100.0,
    "RETEFUENTE_APORTE_VOLUNTARIO_TOPE_UVT_MES": 380.0,
    "TOPE_EMBARGO": 50.0,
}

CONCEPTOS_DEFECTO = {
    "SALARIO": {"nombre": "Sueldo básico", "tipo": "DEVENGADO", "cuenta_puc": "510506", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "AUX_TRANSPORTE": {"nombre": "Auxilio de transporte", "tipo": "DEVENGADO", "cuenta_puc": "510527", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 0},
    "HED": {"nombre": "Horas extra diurnas", "tipo": "DEVENGADO", "cuenta_puc": "510515", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "HEN": {"nombre": "Horas extra nocturnas", "tipo": "DEVENGADO", "cuenta_puc": "510515", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "RNOCT": {"nombre": "Recargo nocturno", "tipo": "DEVENGADO", "cuenta_puc": "510515", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "HODF": {"nombre": "Horas ordinarias dominical/festivo", "tipo": "DEVENGADO", "cuenta_puc": "510515", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "HEDF": {"nombre": "Horas extra diurnas dominical/festivo", "tipo": "DEVENGADO", "cuenta_puc": "510515", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "HONDF": {"nombre": "Horas ordinarias nocturnas dominical/festivo", "tipo": "DEVENGADO", "cuenta_puc": "510515", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "HENDF": {"nombre": "Horas extra nocturnas dominical/festivo", "tipo": "DEVENGADO", "cuenta_puc": "510515", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "BONIFICACION": {"nombre": "Bonificación / incentivo", "tipo": "DEVENGADO", "cuenta_puc": "510506", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "COMISION": {"nombre": "Comisión", "tipo": "DEVENGADO", "cuenta_puc": "520518", "cuenta_puc_credito": None, "afecta_ibc": 1, "afecta_retencion": 1},
    "SALUD_EMPLEADO": {"nombre": "Salud empleado (4%)", "tipo": "DEDUCCION", "cuenta_puc": "237005", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 1},
    "PENSION_EMPLEADO": {"nombre": "Pensión empleado (4%)", "tipo": "DEDUCCION", "cuenta_puc": "238030", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 1},
    "FSP": {"nombre": "Fondo de solidaridad pensional", "tipo": "DEDUCCION", "cuenta_puc": "238095", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 1},
    "RETEFUENTE": {"nombre": "Retención en la fuente", "tipo": "DEDUCCION", "cuenta_puc": "236505", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 0},
    "EMBARGO": {"nombre": "Embargo judicial", "tipo": "DEDUCCION", "cuenta_puc": "237025", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 0},
    "LIBRANZA": {"nombre": "Libranza", "tipo": "DEDUCCION", "cuenta_puc": "237030", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 0},
    "FONDO_EMPLEADOS": {"nombre": "Fondo de empleados", "tipo": "DEDUCCION", "cuenta_puc": "237045", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 0},
    "PRESTAMO_EMPRESA": {"nombre": "Préstamo a la empresa", "tipo": "DEDUCCION", "cuenta_puc": "136590", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 0},
    "SINDICATO": {"nombre": "Aporte sindical", "tipo": "DEDUCCION", "cuenta_puc": "237035", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 0},
    "PREPAGADA": {"nombre": "Salud prepagada", "tipo": "DEDUCCION", "cuenta_puc": "238095", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 1},
    "APORTE_VOLUNTARIO": {"nombre": "Aporte voluntario a pensión", "tipo": "DEDUCCION", "cuenta_puc": "238095", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 1},
    "SALUD_EMPLEADOR": {"nombre": "Salud empleador (8.5%)", "tipo": "APORTE_PATRONAL", "cuenta_puc": "510569", "cuenta_puc_credito": "237005", "afecta_ibc": 0, "afecta_retencion": 0},
    "PENSION_EMPLEADOR": {"nombre": "Pensión empleador (12%)", "tipo": "APORTE_PATRONAL", "cuenta_puc": "510570", "cuenta_puc_credito": "238030", "afecta_ibc": 0, "afecta_retencion": 0},
    "ARL": {"nombre": "ARL", "tipo": "APORTE_PATRONAL", "cuenta_puc": "510568", "cuenta_puc_credito": "237006", "afecta_ibc": 0, "afecta_retencion": 0},
    "SENA": {"nombre": "SENA", "tipo": "APORTE_PATRONAL", "cuenta_puc": "510578", "cuenta_puc_credito": "237010", "afecta_ibc": 0, "afecta_retencion": 0},
    "ICBF": {"nombre": "ICBF", "tipo": "APORTE_PATRONAL", "cuenta_puc": "510575", "cuenta_puc_credito": "237010", "afecta_ibc": 0, "afecta_retencion": 0},
    "CAJA": {"nombre": "Caja de compensación familiar", "tipo": "APORTE_PATRONAL", "cuenta_puc": "510572", "cuenta_puc_credito": "237010", "afecta_ibc": 0, "afecta_retencion": 0},
    "CESANTIAS": {"nombre": "Cesantías", "tipo": "PROVISION", "cuenta_puc": "510530", "cuenta_puc_credito": "251010", "afecta_ibc": 0, "afecta_retencion": 0},
    "INTERESES_CESANTIAS": {"nombre": "Intereses sobre cesantías", "tipo": "PROVISION", "cuenta_puc": "510533", "cuenta_puc_credito": "251505", "afecta_ibc": 0, "afecta_retencion": 0},
    "PRIMA": {"nombre": "Prima de servicios", "tipo": "PROVISION", "cuenta_puc": "510536", "cuenta_puc_credito": "252005", "afecta_ibc": 0, "afecta_retencion": 0},
    "VACACIONES": {"nombre": "Vacaciones", "tipo": "PROVISION", "cuenta_puc": "510539", "cuenta_puc_credito": "252505", "afecta_ibc": 0, "afecta_retencion": 0},
    "NETO": {"nombre": "Neto a pagar", "tipo": "PAGO", "cuenta_puc": "250505", "cuenta_puc_credito": None, "afecta_ibc": 0, "afecta_retencion": 0},
}

TIPOS_PERIODO = ("MENSUAL", "QUINCENAL", "SEMANAL", "PRIMA", "CESANTIAS", "VACACIONES", "OTRO")
ESTADOS_PERIODO_BLOQUEADOS = ("CONTABILIZADO", "PAGADO")


# ---------------------------------------------------------------------------
# Utilidades
# ---------------------------------------------------------------------------

def _decimal(valor):
    if valor is None or valor == "":
        return Decimal("0")
    try:
        return Decimal(str(valor))
    except (TypeError, ValueError, ArithmeticError):
        return Decimal("0")


def _redondear(valor):
    return _decimal(valor).quantize(CENTAVO, rounding=ROUND_HALF_UP)


def _fecha(valor):
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


def _flotante(valor):
    return float(_decimal(valor))


def _serializar(fila):
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
# Parámetros y conceptos
# ---------------------------------------------------------------------------

def obtener_parametros():
    """Devuelve los parámetros legales como diccionario de números."""
    parametros = dict(PARAMETROS_DEFECTO)
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT clave, valor FROM parametros_nomina
                WHERE activo = 1
                  AND (vigencia_desde IS NULL OR vigencia_desde <= CURDATE())
                  AND (vigencia_hasta IS NULL OR vigencia_hasta >= CURDATE())
                """
            )
            for fila in cursor.fetchall():
                parametros[fila["clave"]] = float(fila["valor"])
    finally:
        conexion.close()
    return parametros


def listar_parametros():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_parametro, clave, valor, unidad, descripcion,
                       vigencia_desde, vigencia_hasta, activo, actualizado_en
                FROM parametros_nomina
                ORDER BY clave
                """
            )
            return [_serializar(fila) for fila in cursor.fetchall()]
    finally:
        conexion.close()


def actualizar_parametros(cambios):
    """Actualiza uno o varios parámetros por clave.

    ``cambios`` puede ser un diccionario ``{clave: valor}`` o una lista de
    diccionarios con ``clave`` y ``valor``.
    """
    if isinstance(cambios, dict):
        pares = [{"clave": clave, "valor": valor} for clave, valor in cambios.items()]
    elif isinstance(cambios, list):
        pares = cambios
    else:
        raise ValueError("Formato de parámetros no válido.")
    if not pares:
        raise ValueError("No se recibieron parámetros para actualizar.")

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            actualizados = 0
            for par in pares:
                clave = (par.get("clave") or "").strip()
                if not clave:
                    continue
                valor = par.get("valor")
                try:
                    valor_numerico = Decimal(str(valor))
                except (TypeError, ValueError, ArithmeticError) as error:
                    raise ValueError(f"Valor no válido para {clave}.") from error
                cursor.execute(
                    "UPDATE parametros_nomina SET valor = %s WHERE clave = %s",
                    (valor_numerico, clave),
                )
                actualizados += cursor.rowcount
            conexion.commit()
            return actualizados
    finally:
        conexion.close()


def obtener_conceptos():
    """Catálogo de conceptos indexado por código."""
    conceptos = {codigo: dict(datos) for codigo, datos in CONCEPTOS_DEFECTO.items()}
    for codigo, datos in conceptos.items():
        datos.setdefault("codigo", codigo)
        datos.setdefault("porcentaje", 0)
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT codigo, nombre, tipo, base, porcentaje, cuenta_puc,
                       cuenta_puc_credito, afecta_ibc, afecta_retencion,
                       es_provision, activo, orden
                FROM conceptos_nomina
                WHERE activo = 1
                ORDER BY orden, codigo
                """
            )
            for fila in cursor.fetchall():
                conceptos[fila["codigo"]] = _serializar(fila)
    finally:
        conexion.close()
    return conceptos


def listar_conceptos():
    return sorted(obtener_conceptos().values(), key=lambda c: (c.get("orden") or 0, c.get("codigo") or ""))


# ---------------------------------------------------------------------------
# Novedades de nómina (horas extras, bonificaciones, deducciones)
# ---------------------------------------------------------------------------

def listar_novedades_nomina(id_empleado=None, estado="ACTIVA", fecha_inicio=None,
                            fecha_fin=None):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT n.id_novedad_nomina, n.id_empleado, n.concepto_codigo,
                       n.fecha, n.cantidad, n.valor_unitario, n.valor_total,
                       n.descripcion, n.aplica_ibc, n.aplica_retencion, n.estado,
                       n.creado_en, c.nombre AS concepto, c.tipo,
                       c.cuenta_puc, c.cuenta_puc_credito,
                       e.nombres, e.apellidos
                FROM novedades_nomina n
                JOIN conceptos_nomina c ON c.codigo = n.concepto_codigo
                JOIN empleados e ON e.id_empleado = n.id_empleado
                WHERE 1 = 1
            """
            params = []
            if id_empleado:
                sql += " AND n.id_empleado = %s"
                params.append(id_empleado)
            if estado:
                sql += " AND n.estado = %s"
                params.append(estado)
            if fecha_inicio:
                sql += " AND n.fecha >= %s"
                params.append(_fecha(fecha_inicio))
            if fecha_fin:
                sql += " AND n.fecha <= %s"
                params.append(_fecha(fecha_fin))
            sql += " ORDER BY n.fecha DESC, n.id_novedad_nomina DESC"
            cursor.execute(sql, params)
            return [_serializar(fila) for fila in cursor.fetchall()]
    finally:
        conexion.close()


def crear_novedad_nomina(id_empleado, concepto_codigo, fecha, cantidad=0,
                         valor_unitario=None, valor_total=None,
                         descripcion=None, aplica_ibc=None,
                         aplica_retencion=None, id_usuario=None):
    id_empleado = int(id_empleado or 0)
    if not id_empleado:
        raise ValueError("Selecciona un empleado.")
    concepto_codigo = (concepto_codigo or "").strip().upper()
    if not concepto_codigo:
        raise ValueError("Selecciona un concepto.")
    fecha = _fecha(fecha)

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT id_empleado FROM empleados WHERE id_empleado = %s AND estado = 'ACTIVO'",
                (id_empleado,),
            )
            if not cursor.fetchone():
                raise ValueError("El empleado no existe o está inactivo.")
            cursor.execute(
                "SELECT tipo FROM conceptos_nomina WHERE codigo = %s AND activo = 1",
                (concepto_codigo,),
            )
            concepto = cursor.fetchone()
            if not concepto:
                raise ValueError("El concepto no existe en el catálogo.")
            if (concepto["tipo"] not in ("DEVENGADO", "DEDUCCION")
                    or concepto_codigo in CONCEPTOS_AUTOMATICOS):
                raise ValueError(
                    "Ese concepto se calcula automáticamente y no se registra como novedad."
                )
            cursor.execute(
                """
                INSERT INTO novedades_nomina
                    (id_empleado, concepto_codigo, fecha, cantidad,
                     valor_unitario, valor_total, descripcion, aplica_ibc,
                     aplica_retencion, id_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (
                    id_empleado, concepto_codigo, fecha, _decimal(cantidad),
                    None if valor_unitario in (None, "") else _decimal(valor_unitario),
                    None if valor_total in (None, "") else _decimal(valor_total),
                    (descripcion or "").strip() or None,
                    None if aplica_ibc in (None, "") else int(bool(aplica_ibc)),
                    None if aplica_retencion in (None, "") else int(bool(aplica_retencion)),
                    id_usuario,
                ),
            )
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()


def anular_novedad_nomina(id_novedad, id_usuario=None):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE novedades_nomina SET estado = 'ANULADA' WHERE id_novedad_nomina = %s",
                (id_novedad,),
            )
            conexion.commit()
            if cursor.rowcount == 0:
                raise ValueError("Novedad no encontrada.")
            return cursor.rowcount
    finally:
        conexion.close()


# ---------------------------------------------------------------------------
# Cálculo
# ---------------------------------------------------------------------------

def _linea_concepto(codigo, conceptos, tipo, base, valor, porcentaje=0):
    datos = conceptos.get(codigo) or CONCEPTOS_DEFECTO.get(codigo, {})
    return {
        "codigo": codigo,
        "nombre": datos.get("nombre", codigo),
        "tipo": tipo,
        "base_calculo": float(_redondear(base)),
        "porcentaje": float(_decimal(porcentaje)),
        "valor": float(_redondear(valor)),
        "cuenta_puc": datos.get("cuenta_puc"),
        "cuenta_puc_credito": datos.get("cuenta_puc_credito"),
    }


def _retencion_fuente(base_gravable, uvt, parametros):
    """Aplica la tabla del artículo 383 del Estatuto Tributario.

    La tabla se expresa en UVT y se tomó del liquidador del libro de trabajo.
    """
    if uvt <= 0:
        return Decimal("0")
    base_uvt = base_gravable / uvt
    if base_uvt <= 95:
        impuesto = Decimal("0")
    elif base_uvt <= 150:
        impuesto = (base_uvt - Decimal("95")) * Decimal("0.19")
    elif base_uvt <= 360:
        impuesto = (base_uvt - Decimal("150")) * Decimal("0.28") + Decimal("10")
    elif base_uvt <= 640:
        impuesto = (base_uvt - Decimal("360")) * Decimal("0.33") + Decimal("69")
    elif base_uvt <= 945:
        impuesto = (base_uvt - Decimal("640")) * Decimal("0.35") + Decimal("162")
    elif base_uvt <= 2300:
        impuesto = (base_uvt - Decimal("945")) * Decimal("0.37") + Decimal("268")
    else:
        impuesto = (base_uvt - Decimal("2300")) * Decimal("0.39") + Decimal("770")
    return _redondear(max(impuesto, Decimal("0")) * uvt)


def calcular_nomina_empleado(empleado, parametros=None, conceptos=None,
                             novedades=None, dias_laborados=None):
    """Calcula el devengado, IBC, deducciones, aportes y provisiones.

    Es una función sin acceso a base de datos: recibe el empleado, los
    parámetros, el catálogo de conceptos y las novedades del periodo.
    """
    parametros = {**PARAMETROS_DEFECTO, **(parametros or {})}
    conceptos = conceptos or obtener_conceptos()
    novedades = novedades or []

    empleado = _serializar(empleado)
    salario_base = _decimal(empleado.get("salario_base"))
    dias_solicitados = dias_laborados
    if dias_solicitados in (None, ""):
        dias_solicitados = empleado.get("dias_laborados")
    dias = _decimal(dias_solicitados) if dias_solicitados not in (None, "") else Decimal("30")
    dias = min(max(dias, Decimal("0")), Decimal("30"))
    factor_dias = dias / Decimal("30")

    smmlv = _decimal(parametros.get("SMMLV"))
    uvt = _decimal(parametros.get("UVT"))
    horas_mes = _decimal(parametros.get("HORAS_MES")) or Decimal("210")
    tope_auxilio = _decimal(parametros.get("TOPE_AUXILIO_TRANSPORTE_SMMLV")) * smmlv
    tope_exoneracion = _decimal(parametros.get("TOPE_EXONERACION_SMMLV")) * smmlv

    salario_proporcional = _redondear(salario_base * factor_dias)

    # Auxilio de transporte: no es factor salarial ni entra al IBC.
    auxilio = Decimal("0")
    if not int(empleado.get("salario_integral") or 0):
        auxilio_empleado = empleado.get("auxilio_transporte")
        if auxilio_empleado not in (None, ""):
            auxilio = _redondear(_decimal(auxilio_empleado) * factor_dias)
        elif salario_base <= tope_auxilio:
            auxilio = _redondear(_decimal(parametros.get("AUXILIO_TRANSPORTE")) * factor_dias)

    # Novedades devengadas y deducciones fijas.
    lineas_devengado = []
    lineas_deduccion_fija = []
    horas_extra_total = Decimal("0")
    ibc_extra = Decimal("0")
    ingreso_gravable_extra = Decimal("0")
    valor_hora = salario_base / horas_mes if horas_mes else Decimal("0")
    retencion_manual = None
    porcentaje_embargo = Decimal("0")
    deducciones_retencion = Decimal("0")
    dependientes = int(empleado.get("dependientes") or 0)

    for novedad in novedades:
        codigo = (novedad.get("concepto_codigo") or "").strip().upper()
        if not codigo:
            continue
        concepto = conceptos.get(codigo) or CONCEPTOS_DEFECTO.get(codigo, {})
        tipo = (concepto.get("tipo") or novedad.get("tipo") or "").upper()
        cantidad = _decimal(novedad.get("cantidad"))
        valor_unitario = novedad.get("valor_unitario")
        valor_total = novedad.get("valor_total")
        afecta_ibc = novedad.get("aplica_ibc")
        afecta_retencion = novedad.get("aplica_retencion")
        if afecta_ibc in (None, ""):
            afecta_ibc = int(concepto.get("afecta_ibc") or 0)
        else:
            afecta_ibc = int(bool(afecta_ibc))
        if afecta_retencion in (None, ""):
            afecta_retencion = int(concepto.get("afecta_retencion") or 0)
        else:
            afecta_retencion = int(bool(afecta_retencion))

        if tipo == "DEVENGADO":
            if codigo in CODIGOS_HORAS:
                factor = _decimal(parametros.get(FACTORES_HORAS.get(codigo, ""), concepto.get("porcentaje") or 0))
                if valor_total not in (None, ""):
                    valor = _redondear(valor_total)
                elif valor_unitario not in (None, ""):
                    valor = _redondear(_decimal(valor_unitario) * cantidad)
                else:
                    valor = _redondear(valor_hora * factor * cantidad)
                horas_extra_total += valor
            else:
                if valor_total not in (None, ""):
                    valor = _redondear(valor_total)
                elif valor_unitario not in (None, ""):
                    valor = _redondear(_decimal(valor_unitario) * cantidad)
                else:
                    valor = Decimal("0")
            if valor <= 0:
                continue
            linea = _linea_concepto(codigo, conceptos, "DEVENGADO", salario_proporcional, valor)
            lineas_devengado.append(linea)
            if afecta_ibc:
                ibc_extra += valor
            if afecta_retencion:
                ingreso_gravable_extra += valor
        elif tipo == "DEDUCCION":
            if codigo == "RETEFUENTE":
                retencion_manual = (
                    _decimal(valor_total) if valor_total not in (None, "") else None
                )
                continue
            if codigo == "EMBARGO" and valor_total in (None, ""):
                porcentaje_embargo = cantidad if cantidad > 0 else Decimal("0")
                continue
            if valor_total not in (None, ""):
                valor = _redondear(valor_total)
            elif valor_unitario not in (None, ""):
                valor = _redondear(_decimal(valor_unitario) * cantidad)
            else:
                valor = Decimal("0")
            if valor <= 0:
                continue
            lineas_deduccion_fija.append(
                _linea_concepto(codigo, conceptos, "DEDUCCION", salario_proporcional, valor)
            )
            # PREPAGADA y APORTE_VOLUNTARIO se aplican después con sus topes
            # legales; no deben sumarse otra vez a las deducciones imputables.
            if afecta_retencion and codigo not in ("PREPAGADA", "APORTE_VOLUNTARIO"):
                deducciones_retencion += valor

    total_devengado = salario_proporcional + auxilio + sum(
        _decimal(linea["valor"]) for linea in lineas_devengado
    )
    total_devengado = _redondear(total_devengado)

    # IBC: salario proporcional + conceptos salariales, con tope legal.
    ibc = salario_proporcional + ibc_extra
    tope_ibc = _decimal(parametros.get("TOPE_IBC_SMMLV")) * smmlv
    if tope_ibc > 0:
        ibc = min(ibc, tope_ibc)
    ibc = _redondear(max(ibc, Decimal("0")))

    # Deducciones legales.
    tasa_salud = _decimal(parametros.get("SALUD_EMPLEADO"))
    tasa_pension = _decimal(parametros.get("PENSION_EMPLEADO"))
    salud = _redondear(ibc * tasa_salud / Decimal("100"))
    pension = _redondear(ibc * tasa_pension / Decimal("100"))

    # Fondo de solidaridad pensional por tramos de SMMLV.
    fsp = Decimal("0")
    if smmlv > 0:
        if ibc >= _decimal(parametros.get("FSP_UMBRAL_4_SMMLV")) * smmlv:
            tasa_fsp = _decimal(parametros.get("FSP_TASA_4"))
        elif ibc >= _decimal(parametros.get("FSP_UMBRAL_3_SMMLV")) * smmlv:
            tasa_fsp = _decimal(parametros.get("FSP_TASA_3"))
        elif ibc >= _decimal(parametros.get("FSP_UMBRAL_2_SMMLV")) * smmlv:
            tasa_fsp = _decimal(parametros.get("FSP_TASA_2"))
        elif ibc >= _decimal(parametros.get("FSP_UMBRAL_1_SMMLV")) * smmlv:
            tasa_fsp = _decimal(parametros.get("FSP_TASA_1"))
        else:
            tasa_fsp = Decimal("0")
        fsp = _redondear(ibc * tasa_fsp / Decimal("100"))

    # Retención en la fuente (art. 383 ET), usando el mismo IBC y deducciones.
    ingreso_gravable = salario_proporcional + ingreso_gravable_extra
    renta_liquida = max(ingreso_gravable - salud - pension - fsp, Decimal("0"))
    deduccion_dependientes_10 = min(
        renta_liquida * _decimal(parametros.get("RETEFUENTE_DEPENDIENTES")) / Decimal("100"),
        _decimal(parametros.get("RETEFUENTE_DEPENDIENTES_TOPE_UVT_MES")) * uvt,
    )
    deduccion_dependientes_72 = min(
        Decimal(dependientes) * _decimal(parametros.get("RETEFUENTE_DEPENDIENTES_UVT_MES")) * uvt,
        _decimal(parametros.get("RETEFUENTE_DEPENDIENTES_TOPE_UVT_MES")) * uvt,
    )
    deduccion_prepagada = min(
        sum(_decimal(linea["valor"]) for linea in lineas_deduccion_fija if linea["codigo"] == "PREPAGADA"),
        _decimal(parametros.get("RETEFUENTE_PREPAGADA_TOPE_UVT_MES")) * uvt,
    )
    deduccion_voluntaria = min(
        sum(_decimal(linea["valor"]) for linea in lineas_deduccion_fija if linea["codigo"] == "APORTE_VOLUNTARIO"),
        _decimal(parametros.get("RETEFUENTE_APORTE_VOLUNTARIO_TOPE_UVT_MES")) * uvt,
    )
    deducciones_imputables = (
        deduccion_dependientes_10 + deduccion_dependientes_72 +
        deduccion_prepagada + deduccion_voluntaria + deducciones_retencion
    )
    base_renta_exenta = max(renta_liquida - deducciones_imputables, Decimal("0"))
    renta_exenta = min(
        base_renta_exenta * _decimal(parametros.get("RETEFUENTE_EXENTO")) / Decimal("100"),
        _decimal(parametros.get("RETEFUENTE_TOPE_EXENTO_UVT_MES")) * uvt,
    )
    base_gravable = max(base_renta_exenta - renta_exenta, Decimal("0"))
    if retencion_manual is not None and retencion_manual > 0:
        retencion = _redondear(retencion_manual)
    else:
        retencion = _retencion_fuente(base_gravable, uvt, parametros)

    # Embargo: porcentaje sobre el disponible después de aportes y deducciones.
    # Se acota al tope legal configurable para no descontar más de lo permitido.
    tope_embargo = _decimal(parametros.get("TOPE_EMBARGO")) or Decimal("50")
    porcentaje_embargo = min(max(porcentaje_embargo, Decimal("0")), tope_embargo)
    deducciones_antes_embargo = sum(_decimal(linea["valor"]) for linea in lineas_deduccion_fija)
    disponible_embargo = max(
        total_devengado - salud - pension - fsp - retencion - deducciones_antes_embargo,
        Decimal("0"),
    )
    embargo = _redondear(disponible_embargo * porcentaje_embargo / Decimal("100")) if porcentaje_embargo > 0 else Decimal("0")

    lineas_deduccion = [
        _linea_concepto("SALUD_EMPLEADO", conceptos, "DEDUCCION", ibc, salud, tasa_salud),
        _linea_concepto("PENSION_EMPLEADO", conceptos, "DEDUCCION", ibc, pension, tasa_pension),
    ]
    if fsp > 0:
        lineas_deduccion.append(_linea_concepto("FSP", conceptos, "DEDUCCION", ibc, fsp, Decimal("0")))
    if retencion > 0:
        lineas_deduccion.append(_linea_concepto("RETEFUENTE", conceptos, "DEDUCCION", base_gravable, retencion))
    lineas_deduccion.extend(lineas_deduccion_fija)
    if embargo > 0:
        lineas_deduccion.append(_linea_concepto("EMBARGO", conceptos, "DEDUCCION", disponible_embargo, embargo, porcentaje_embargo))

    total_deducciones = sum(_decimal(linea["valor"]) for linea in lineas_deduccion)
    total_deducciones = _redondear(total_deducciones)
    neto_pagar = _redondear(total_devengado - total_deducciones)

    # Aportes patronales.
    exonerado_salud = bool(int(empleado.get("exonerado_salud") or 0)) or (
        tope_exoneracion > 0 and salario_base < tope_exoneracion
    )
    exonerado_parafiscales = bool(int(empleado.get("exonerado_parafiscales") or 0)) or (
        tope_exoneracion > 0 and salario_base < tope_exoneracion
    )

    lineas_aportes = []
    tasa_salud_empleador = Decimal("0") if exonerado_salud else _decimal(parametros.get("SALUD_EMPLEADOR"))
    if tasa_salud_empleador > 0:
        valor = _redondear(ibc * tasa_salud_empleador / Decimal("100"))
        lineas_aportes.append(_linea_concepto("SALUD_EMPLEADOR", conceptos, "APORTE_PATRONAL", ibc, valor, tasa_salud_empleador))

    tasa_pension_empleador = _decimal(parametros.get("PENSION_EMPLEADOR"))
    valor_pension = _redondear(ibc * tasa_pension_empleador / Decimal("100"))
    lineas_aportes.append(_linea_concepto("PENSION_EMPLEADOR", conceptos, "APORTE_PATRONAL", ibc, valor_pension, tasa_pension_empleador))

    nivel_arl = int(empleado.get("riesgo_arl") or 1)
    nivel_arl = min(max(nivel_arl, 1), 5)
    tasa_arl = _decimal(parametros.get(f"ARL_NIVEL_{nivel_arl}"))
    valor_arl = _redondear(ibc * tasa_arl / Decimal("100"))
    lineas_aportes.append(_linea_concepto("ARL", conceptos, "APORTE_PATRONAL", ibc, valor_arl, tasa_arl))

    if not exonerado_parafiscales:
        tasa_sena = _decimal(parametros.get("SENA"))
        tasa_icbf = _decimal(parametros.get("ICBF"))
        lineas_aportes.append(_linea_concepto("SENA", conceptos, "APORTE_PATRONAL", ibc, _redondear(ibc * tasa_sena / Decimal("100")), tasa_sena))
        lineas_aportes.append(_linea_concepto("ICBF", conceptos, "APORTE_PATRONAL", ibc, _redondear(ibc * tasa_icbf / Decimal("100")), tasa_icbf))

    tasa_caja = _decimal(parametros.get("CAJA_COMPENSACION"))
    lineas_aportes.append(_linea_concepto("CAJA", conceptos, "APORTE_PATRONAL", ibc, _redondear(ibc * tasa_caja / Decimal("100")), tasa_caja))
    total_aportes = _redondear(sum(_decimal(linea["valor"]) for linea in lineas_aportes))

    # Provisiones. Si el salario es integral, las prestaciones ya están incluidas.
    lineas_provisiones = []
    if not int(empleado.get("salario_integral") or 0):
        base_prestaciones = salario_proporcional + sum(
            _decimal(linea["valor"]) for linea in lineas_devengado
        )
        tasa_cesantias = _decimal(parametros.get("CESANTIAS"))
        cesantias = _redondear(base_prestaciones * tasa_cesantias / Decimal("100"))
        tasa_intereses = _decimal(parametros.get("INTERESES_CESANTIAS"))
        intereses = _redondear(cesantias * tasa_intereses / Decimal("100"))
        tasa_prima = _decimal(parametros.get("PRIMA"))
        prima = _redondear(base_prestaciones * tasa_prima / Decimal("100"))
        tasa_vacaciones = _decimal(parametros.get("VACACIONES"))
        vacaciones = _redondear(salario_proporcional * tasa_vacaciones / Decimal("100"))

        if cesantias > 0:
            lineas_provisiones.append(_linea_concepto("CESANTIAS", conceptos, "PROVISION", base_prestaciones, cesantias, tasa_cesantias))
        if intereses > 0:
            lineas_provisiones.append(_linea_concepto("INTERESES_CESANTIAS", conceptos, "PROVISION", cesantias, intereses, tasa_intereses))
        if prima > 0:
            lineas_provisiones.append(_linea_concepto("PRIMA", conceptos, "PROVISION", base_prestaciones, prima, tasa_prima))
        if vacaciones > 0:
            lineas_provisiones.append(_linea_concepto("VACACIONES", conceptos, "PROVISION", salario_proporcional, vacaciones, tasa_vacaciones))

    total_provisiones = _redondear(sum(_decimal(linea["valor"]) for linea in lineas_provisiones))

    lineas_devengado.insert(0, _linea_concepto("SALARIO", conceptos, "DEVENGADO", salario_proporcional, salario_proporcional))
    if auxilio > 0:
        lineas_devengado.insert(1, _linea_concepto("AUX_TRANSPORTE", conceptos, "DEVENGADO", auxilio, auxilio))
    lineas_neto = [_linea_concepto("NETO", conceptos, "PAGO", neto_pagar, neto_pagar)]

    return {
        "empleado": {
            "id_empleado": empleado.get("id_empleado"),
            "nombre": f"{empleado.get('nombres', '')} {empleado.get('apellidos', '')}".strip(),
            "documento": empleado.get("documento"),
            "cargo": empleado.get("cargo"),
        },
        "dias_laborados": float(dias),
        "salario_base": float(salario_base),
        "salario_proporcional": float(salario_proporcional),
        "auxilio_transporte": float(auxilio),
        "total_horas_extra": float(horas_extra_total),
        "total_devengado": float(total_devengado),
        "ibc": float(ibc),
        "deducciones": lineas_deduccion,
        "total_deducciones": float(total_deducciones),
        "aportes": lineas_aportes,
        "total_aportes": float(total_aportes),
        "provisiones": lineas_provisiones,
        "total_provisiones": float(total_provisiones),
        "neto_pagar": float(neto_pagar),
        "conceptos": lineas_devengado + lineas_deduccion + lineas_aportes + lineas_provisiones + lineas_neto,
    }


# ---------------------------------------------------------------------------
# Liquidación de periodos
# ---------------------------------------------------------------------------

def _obtener_empleado(cursor, id_empleado):
    cursor.execute("SELECT * FROM empleados WHERE id_empleado = %s", (id_empleado,))
    return cursor.fetchone()


def _novedades_para_periodo(cursor, id_empleado, fecha_inicio, fecha_fin):
    cursor.execute(
        """
        SELECT n.concepto_codigo, n.fecha, n.cantidad, n.valor_unitario,
               n.valor_total, n.descripcion, n.aplica_ibc, n.aplica_retencion,
               c.nombre AS concepto, c.tipo, c.cuenta_puc,
               c.cuenta_puc_credito, c.afecta_ibc, c.afecta_retencion
        FROM novedades_nomina n
        JOIN conceptos_nomina c ON c.codigo = n.concepto_codigo
        WHERE n.id_empleado = %s AND n.estado = 'ACTIVA'
          AND n.fecha BETWEEN %s AND %s
        ORDER BY n.fecha, n.id_novedad_nomina
        """,
        (id_empleado, fecha_inicio, fecha_fin),
    )
    return cursor.fetchall()


def _ultimo_dia_mes(fecha):
    """Devuelve el último día calendario del mes de ``fecha``."""
    siguiente_mes = (fecha.replace(day=28) + timedelta(days=4)).replace(day=1)
    return siguiente_mes - timedelta(days=1)


def _dias_base_periodo(empleado, fecha_inicio, fecha_fin):
    """Días que cubre el periodo para el empleado según ingreso y retiro.

    Un mes completo se liquida como 30 días, sin importar que el mes tenga
    28, 29, 30 o 31. Los periodos parciales usan los días calendario.
    """
    inicio = fecha_inicio
    if empleado.get("fecha_ingreso"):
        inicio = max(inicio, _fecha(empleado["fecha_ingreso"]))
    fin = fecha_fin
    if empleado.get("fecha_retiro"):
        fin = min(fin, _fecha(empleado["fecha_retiro"]))
    if inicio > fin:
        return Decimal("0")
    if (inicio == fecha_inicio and fin == fecha_fin
            and fecha_inicio.day == 1
            and fecha_fin == _ultimo_dia_mes(fecha_fin)):
        return Decimal("30")
    return Decimal(min((fin - inicio).days + 1, 30))


def _dias_ausencia_aprobada(cursor, id_empleado, fecha_inicio, fecha_fin):
    """Días de ausencia no remunerada aprobados dentro del periodo."""
    cursor.execute(
        """
        SELECT COALESCE(SUM(
            DATEDIFF(LEAST(n.fecha_fin, %s), GREATEST(n.fecha_inicio, %s)) + 1
        ), 0) AS dias
        FROM novedades n
        WHERE n.id_empleado = %s
          AND n.tipo = 'AUSENCIA'
          AND n.estado = 'APROBADA'
          AND n.fecha_inicio <= %s
          AND n.fecha_fin >= %s
        """,
        (fecha_fin, fecha_inicio, id_empleado, fecha_fin, fecha_inicio),
    )
    return _decimal((cursor.fetchone() or {}).get("dias"))


def liquidar_periodo(fecha_inicio, fecha_fin, tipo="MENSUAL", nombre=None,
                     id_usuario=None, id_empleado=None):
    """Calcula y guarda la nómina de un periodo para todos los empleados activos."""
    fecha_inicio = _fecha(fecha_inicio)
    fecha_fin = _fecha(fecha_fin)
    if fecha_fin < fecha_inicio:
        raise ValueError("La fecha final no puede ser anterior a la inicial.")
    tipo = (tipo or "MENSUAL").upper()
    if tipo not in TIPOS_PERIODO:
        raise ValueError("Tipo de periodo no válido.")

    parametros = obtener_parametros()
    conceptos = obtener_conceptos()
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            if id_empleado:
                cursor.execute(
                    "SELECT * FROM empleados WHERE id_empleado = %s AND estado = 'ACTIVO'",
                    (id_empleado,),
                )
            else:
                cursor.execute("SELECT * FROM empleados WHERE estado = 'ACTIVO' ORDER BY id_empleado")
            empleados = cursor.fetchall()
            if not empleados:
                raise ValueError("No hay empleados activos para liquidar.")

            # Reutilizar el periodo si ya existe y no está contabilizado.
            cursor.execute(
                """
                SELECT id_periodo, estado FROM nomina_periodos
                WHERE fecha_inicio = %s AND fecha_fin = %s AND tipo = %s
                """,
                (fecha_inicio, fecha_fin, tipo),
            )
            existente = cursor.fetchone()
            if existente:
                if existente["estado"] in ESTADOS_PERIODO_BLOQUEADOS:
                    raise ValueError("El periodo ya está contabilizado o pagado y no se puede recalcular.")
                id_periodo = existente["id_periodo"]
                cursor.execute("DELETE FROM nomina_detalle WHERE id_periodo = %s", (id_periodo,))
                cursor.execute(
                    """
                    UPDATE nomina_periodos
                    SET nombre = %s, estado = 'CALCULADO', total_devengado = 0,
                        total_deducciones = 0, total_aportes = 0,
                        total_provisiones = 0, total_neto = 0,
                        id_usuario = %s
                    WHERE id_periodo = %s
                    """,
                    ((nombre or f"Nómina {fecha_inicio} a {fecha_fin}"), id_usuario, id_periodo),
                )
            else:
                cursor.execute(
                    """
                    INSERT INTO nomina_periodos
                        (nombre, tipo, fecha_inicio, fecha_fin, fecha_pago, estado,
                         id_usuario)
                    VALUES (%s, %s, %s, %s, %s, 'CALCULADO', %s)
                    """,
                    (
                        nombre or f"Nómina {fecha_inicio} a {fecha_fin}", tipo,
                        fecha_inicio, fecha_fin, fecha_fin, id_usuario,
                    ),
                )
                id_periodo = cursor.lastrowid

            detalles = []
            for empleado in empleados:
                novedades = _novedades_para_periodo(
                    cursor, empleado["id_empleado"], fecha_inicio, fecha_fin
                )
                dias_base = _dias_base_periodo(empleado, fecha_inicio, fecha_fin)
                dias_ausencia = _dias_ausencia_aprobada(
                    cursor, empleado["id_empleado"], fecha_inicio, fecha_fin
                )
                dias_liquidar = max(Decimal("0"), dias_base - dias_ausencia)
                calculo = calcular_nomina_empleado(
                    empleado, parametros, conceptos, novedades,
                    dias_laborados=dias_liquidar,
                )
                cursor.execute(
                    """
                    INSERT INTO nomina_detalle
                        (id_periodo, id_empleado, dias_laborados, salario_base,
                         auxilio_transporte, total_horas_extra, total_devengado,
                         ibc, total_deducciones, total_aportes,
                         total_provisiones, neto_pagar)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (
                        id_periodo, empleado["id_empleado"],
                        calculo["dias_laborados"], calculo["salario_base"],
                        calculo["auxilio_transporte"], calculo["total_horas_extra"],
                        calculo["total_devengado"], calculo["ibc"],
                        calculo["total_deducciones"], calculo["total_aportes"],
                        calculo["total_provisiones"], calculo["neto_pagar"],
                    ),
                )
                id_detalle = cursor.lastrowid
                cursor.executemany(
                    """
                    INSERT INTO nomina_detalle_conceptos
                        (id_detalle, codigo_concepto, nombre, tipo, base_calculo,
                         porcentaje, valor, cuenta_puc, cuenta_puc_credito)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    [
                        (
                            id_detalle, linea["codigo"], linea["nombre"], linea["tipo"],
                            linea["base_calculo"], linea["porcentaje"], linea["valor"],
                            linea["cuenta_puc"], linea["cuenta_puc_credito"],
                        )
                        for linea in calculo["conceptos"]
                    ],
                )
                detalles.append(calculo["empleado"] | {"id_detalle": id_detalle, **calculo})

            total_devengado = sum(_decimal(d["total_devengado"]) for d in detalles)
            total_deducciones = sum(_decimal(d["total_deducciones"]) for d in detalles)
            total_aportes = sum(_decimal(d["total_aportes"]) for d in detalles)
            total_provisiones = sum(_decimal(d["total_provisiones"]) for d in detalles)
            total_neto = sum(_decimal(d["neto_pagar"]) for d in detalles)

            cursor.execute(
                """
                UPDATE nomina_periodos
                SET total_devengado = %s, total_deducciones = %s,
                    total_aportes = %s, total_provisiones = %s, total_neto = %s
                WHERE id_periodo = %s
                """,
                (
                    _redondear(total_devengado), _redondear(total_deducciones),
                    _redondear(total_aportes), _redondear(total_provisiones),
                    _redondear(total_neto), id_periodo,
                ),
            )

            # Compatibilidad con el historial anterior (tabla ``nomina``).
            periodo_legacy = fecha_inicio.strftime("%Y-%m")
            ids = [d["id_empleado"] for d in detalles]
            if ids:
                marcadores = ",".join(["%s"] * len(ids))
                cursor.execute(
                    f"DELETE FROM nomina WHERE periodo = %s AND id_empleado IN ({marcadores})",
                    [periodo_legacy, *ids],
                )
            for detalle in detalles:
                cursor.execute(
                    """
                    INSERT INTO nomina
                        (id_empleado, periodo, salario_base, total_deducciones,
                         total_aportes, salario_neto)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (
                        detalle["id_empleado"], periodo_legacy,
                        detalle["total_devengado"], detalle["total_deducciones"],
                        detalle["total_aportes"] + detalle["total_provisiones"],
                        detalle["neto_pagar"],
                    ),
                )

            conexion.commit()
            return {
                "id_periodo": id_periodo,
                "nombre": nombre or f"Nómina {fecha_inicio} a {fecha_fin}",
                "fecha_inicio": fecha_inicio.strftime("%Y-%m-%d"),
                "fecha_fin": fecha_fin.strftime("%Y-%m-%d"),
                "total_devengado": float(_redondear(total_devengado)),
                "total_deducciones": float(_redondear(total_deducciones)),
                "total_aportes": float(_redondear(total_aportes)),
                "total_provisiones": float(_redondear(total_provisiones)),
                "total_neto": float(_redondear(total_neto)),
                "empleados": len(detalles),
            }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def listar_periodos(limite=50):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.id_periodo, p.nombre, p.tipo, p.fecha_inicio, p.fecha_fin,
                       p.fecha_pago, p.estado, p.total_devengado,
                       p.total_deducciones, p.total_aportes, p.total_provisiones,
                       p.total_neto, p.id_comprobante, p.creado_en,
                       COUNT(d.id_detalle) AS empleados
                FROM nomina_periodos p
                LEFT JOIN nomina_detalle d ON d.id_periodo = p.id_periodo
                GROUP BY p.id_periodo
                ORDER BY p.fecha_fin DESC, p.id_periodo DESC
                LIMIT %s
                """,
                (max(1, min(int(limite or 50), 200)),),
            )
            return [_serializar(fila) for fila in cursor.fetchall()]
    finally:
        conexion.close()


def obtener_periodo(id_periodo):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT p.*, u.nombre AS usuario, c.numero AS comprobante_numero
                FROM nomina_periodos p
                LEFT JOIN usuarios u ON u.id_usuario = p.id_usuario
                LEFT JOIN comprobantes c ON c.id_comprobante = p.id_comprobante
                WHERE p.id_periodo = %s
                """,
                (id_periodo,),
            )
            periodo = cursor.fetchone()
            if not periodo:
                return None
            cursor.execute(
                """
                SELECT d.*, e.nombres, e.apellidos, e.documento, e.cargo
                FROM nomina_detalle d
                JOIN empleados e ON e.id_empleado = d.id_empleado
                WHERE d.id_periodo = %s
                ORDER BY e.apellidos, e.nombres
                """,
                (id_periodo,),
            )
            detalles = cursor.fetchall()
            resultado = _serializar(periodo)
            resultado["detalles"] = []
            for detalle in detalles:
                item = _serializar(detalle)
                cursor.execute(
                    """
                    SELECT codigo_concepto, nombre, tipo, base_calculo,
                           porcentaje, valor, cuenta_puc, cuenta_puc_credito
                    FROM nomina_detalle_conceptos
                    WHERE id_detalle = %s
                    ORDER BY id_detalle_concepto
                    """,
                    (detalle["id_detalle"],),
                )
                item["conceptos"] = [_serializar(fila) for fila in cursor.fetchall()]
                item["empleado"] = f"{detalle['nombres']} {detalle['apellidos']}".strip()
                resultado["detalles"].append(item)
            return resultado
    finally:
        conexion.close()


def contabilizar_periodo(id_periodo, id_usuario=None):
    """Genera el comprobante contable de nómina del periodo."""
    from services.comprobante_service import crear_comprobante  # import local

    periodo = obtener_periodo(id_periodo)
    if not periodo:
        raise ValueError("Periodo de nómina no encontrado.")
    if periodo.get("id_comprobante"):
        raise ValueError("El periodo ya tiene un comprobante contable.")
    if periodo["estado"] in ESTADOS_PERIODO_BLOQUEADOS:
        raise ValueError("El periodo ya está contabilizado o pagado.")

    # Agregar por cuenta y concepto para no generar cientos de líneas.
    movimientos = {}
    for detalle in periodo["detalles"]:
        for linea in detalle["conceptos"]:
            tipo = (linea.get("tipo") or "").upper()
            valor = _decimal(linea.get("valor"))
            if valor <= 0:
                continue
            if tipo == "DEVENGADO":
                clave = (linea.get("cuenta_puc"), linea.get("nombre"), "D")
                movimientos[clave] = movimientos.get(clave, Decimal("0")) + valor
            elif tipo in ("DEDUCCION", "PAGO"):
                clave = (linea.get("cuenta_puc"), linea.get("nombre"), "C")
                movimientos[clave] = movimientos.get(clave, Decimal("0")) + valor
            elif tipo in ("APORTE_PATRONAL", "PROVISION"):
                clave_d = (linea.get("cuenta_puc"), linea.get("nombre"), "D")
                clave_c = (linea.get("cuenta_puc_credito"), linea.get("nombre"), "C")
                movimientos[clave_d] = movimientos.get(clave_d, Decimal("0")) + valor
                movimientos[clave_c] = movimientos.get(clave_c, Decimal("0")) + valor

    lineas = []
    for (cuenta, descripcion, lado), valor in sorted(movimientos.items(), key=lambda item: (item[0][0] or "", item[0][2])):
        if not cuenta or valor <= 0:
            continue
        lineas.append({
            "codigo": cuenta,
            "descripcion": descripcion,
            "debito": float(valor) if lado == "D" else 0,
            "credito": float(valor) if lado == "C" else 0,
        })

    if len(lineas) < 2:
        raise ValueError("No hay movimientos suficientes para contabilizar la nómina.")

    conexion = obtener_conexion()
    try:
        resultado = crear_comprobante(
            tipo="NOMINA",
            fecha=periodo.get("fecha_pago") or periodo["fecha_fin"],
            descripcion=f"{periodo['nombre']} ({periodo['fecha_inicio']} a {periodo['fecha_fin']})",
            lineas=lineas,
            id_usuario=id_usuario,
            origen="NOMINA",
            id_origen=str(id_periodo),
            conexion=conexion,
        )
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                UPDATE nomina_periodos
                SET estado = 'CONTABILIZADO', id_comprobante = %s
                WHERE id_periodo = %s
                """,
                (resultado["id_comprobante"], id_periodo),
            )
        conexion.commit()
        return resultado
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def resumen_nomina_nuevo(fecha_inicio=None, fecha_fin=None):
    """Resumen para consolidación contable a partir de los periodos nuevos."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT
                    COALESCE(SUM(p.total_devengado), 0) AS total_devengado,
                    COALESCE(SUM(p.total_deducciones), 0) AS total_deducciones,
                    COALESCE(SUM(p.total_aportes), 0) AS total_aportes,
                    COALESCE(SUM(p.total_provisiones), 0) AS total_provisiones
                FROM nomina_periodos p
                WHERE p.estado IN ('CALCULADO','CONTABILIZADO','PAGADO')
            """
            params = []
            if fecha_inicio:
                sql += " AND p.fecha_fin >= %s"
                params.append(_fecha(fecha_inicio))
            if fecha_fin:
                sql += " AND p.fecha_inicio <= %s"
                params.append(_fecha(fecha_fin))
            cursor.execute(sql, params)
            fila = cursor.fetchone() or {}
            devengado = float(fila.get("total_devengado") or 0)
            deducciones = float(fila.get("total_deducciones") or 0)
            aportes = float(fila.get("total_aportes") or 0)
            provisiones = float(fila.get("total_provisiones") or 0)
            return {
                "costo_nomina": devengado + aportes + provisiones,
                "deducciones": deducciones,
                "total_devengado": devengado,
                "costo_patronal": aportes + provisiones,
                "total_aportes": aportes,
                "total_provisiones": provisiones,
            }
    finally:
        conexion.close()


def hay_periodos_nuevos():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT COUNT(*) AS total FROM nomina_periodos")
            return bool(cursor.fetchone()["total"])
    finally:
        conexion.close()
