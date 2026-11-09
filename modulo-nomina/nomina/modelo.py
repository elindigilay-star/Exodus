from database.connection import obtener_conexion


# ---------------------------------------------------------------
# RF-6 / RF-7: Empleados
# ---------------------------------------------------------------

def listar_empleados(estado=None):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            if estado:
                cursor.execute(
                    "SELECT * FROM empleados WHERE estado = %s ORDER BY id_empleado DESC",
                    (estado,),
                )
            else:
                cursor.execute("SELECT * FROM empleados ORDER BY id_empleado DESC")
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_empleado(id_empleado, solo_activo=False):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = "SELECT * FROM empleados WHERE id_empleado = %s"
            if solo_activo:
                sql += " AND estado = 'ACTIVO'"
            cursor.execute(sql, (id_empleado,))
            return cursor.fetchone()
    finally:
        conexion.close()


def obtener_empleado_por_documento(documento):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM empleados WHERE documento = %s", (documento,))
            return cursor.fetchone()
    finally:
        conexion.close()


def crear_empleado(nombres, apellidos, documento, cargo, salario_base, fecha_ingreso,
                   **extras):
    """Registra un empleado con los campos opcionales del motor de nómina.

    Los campos extra (tipo de contrato, auxilio de transporte, riesgo ARL,
    exoneraciones, etc.) se guardan solo si la columna existe, para mantener
    compatibilidad con bases creadas antes de ampliar la tabla.
    """
    columnas_validas = {
        'tipo_documento', 'email', 'telefono', 'direccion', 'ciudad',
        'fecha_nacimiento', 'sexo', 'estado_civil', 'tipo_contrato',
        'fecha_retiro', 'salario_integral', 'auxilio_transporte', 'riesgo_arl',
        'exonerado_salud', 'exonerado_parafiscales', 'centro_costo', 'banco',
        'cuenta_banco', 'dependientes',
    }
    campos = ['nombres', 'apellidos', 'documento', 'cargo', 'salario_base',
              'fecha_ingreso']
    valores = [nombres, apellidos, documento, cargo, salario_base, fecha_ingreso]
    for clave, valor in extras.items():
        if clave in columnas_validas and valor not in (None, ''):
            campos.append(clave)
            valores.append(valor)

    marcadores = ', '.join(['%s'] * len(campos))
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                f"INSERT INTO empleados ({', '.join(campos)}) VALUES ({marcadores})",
                valores,
            )
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()


def actualizar_empleado(id_empleado, **campos):
    """Actualiza solo los campos permitidos de un empleado."""
    permitidos = {
        'nombres', 'apellidos', 'documento', 'tipo_documento', 'cargo', 'email',
        'telefono', 'direccion', 'ciudad', 'fecha_nacimiento', 'sexo',
        'estado_civil', 'tipo_contrato', 'fecha_ingreso', 'fecha_retiro',
        'salario_base', 'salario_integral', 'auxilio_transporte', 'riesgo_arl',
        'exonerado_salud', 'exonerado_parafiscales', 'centro_costo', 'banco',
        'cuenta_banco', 'dependientes', 'estado',
    }
    asignaciones = []
    valores = []
    for clave, valor in campos.items():
        if clave in permitidos:
            asignaciones.append(f"{clave} = %s")
            valores.append(valor)
    if not asignaciones:
        return 0
    valores.append(id_empleado)
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                f"UPDATE empleados SET {', '.join(asignaciones)} WHERE id_empleado = %s",
                valores,
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


def desactivar_empleado(id_empleado):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE empleados SET estado = 'INACTIVO' WHERE id_empleado = %s",
                (id_empleado,),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


# ---------------------------------------------------------------
# RF-8: Nómina (deducciones, aportes y cálculo)
# ---------------------------------------------------------------

def listar_deducciones_activas():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM deducciones WHERE activo = 1")
            return cursor.fetchall()
    finally:
        conexion.close()


def listar_aportes_activos():
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM aportes WHERE activo = 1")
            return cursor.fetchall()
    finally:
        conexion.close()


def guardar_nomina(id_empleado, periodo, salario_base, total_deducciones,
                   total_aportes, salario_neto):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO nomina
                    (id_empleado, periodo, salario_base,
                     total_deducciones, total_aportes, salario_neto)
                VALUES (%s, %s, %s, %s, %s, %s)
                """,
                (id_empleado, periodo, salario_base, total_deducciones,
                 total_aportes, salario_neto),
            )
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()


def listar_historial_nomina(limite=50):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT n.id_nomina, n.periodo, n.salario_base, n.total_deducciones,
                       n.total_aportes, n.salario_neto, n.generado_en,
                       e.nombres, e.apellidos
                FROM nomina n
                JOIN empleados e ON e.id_empleado = n.id_empleado
                ORDER BY n.generado_en DESC, n.id_nomina DESC
                LIMIT %s
                """,
                (limite,),
            )
            return cursor.fetchall()
    finally:
        conexion.close()


# ---------------------------------------------------------------
# RF-9: Ausencias, vacaciones y permisos
# ---------------------------------------------------------------

def existe_novedad_cruzada(id_empleado, fecha_inicio, fecha_fin):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT id_novedad FROM novedades
                WHERE id_empleado = %s
                  AND estado IN ('PENDIENTE','APROBADA')
                  AND NOT (fecha_fin < %s OR fecha_inicio > %s)
                """,
                (id_empleado, fecha_inicio, fecha_fin),
            )
            return cursor.fetchone() is not None
    finally:
        conexion.close()


def crear_novedad(id_empleado, tipo, fecha_inicio, fecha_fin, motivo):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO novedades (id_empleado, tipo, fecha_inicio, fecha_fin, motivo)
                VALUES (%s, %s, %s, %s, %s)
                """,
                (id_empleado, tipo, fecha_inicio, fecha_fin, motivo),
            )
            conexion.commit()
            return cursor.lastrowid
    finally:
        conexion.close()


def listar_novedades(estado=None):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql = """
                SELECT n.id_novedad, n.tipo, n.fecha_inicio, n.fecha_fin, n.motivo,
                       n.estado, e.nombres, e.apellidos
                FROM novedades n
                JOIN empleados e ON e.id_empleado = n.id_empleado
            """
            params = []
            if estado:
                sql += " WHERE n.estado = %s"
                params.append(estado)
            sql += " ORDER BY n.creado_en DESC, n.id_novedad DESC"
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conexion.close()


def actualizar_estado_novedad(id_novedad, estado):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "UPDATE novedades SET estado = %s WHERE id_novedad = %s",
                (estado, id_novedad),
            )
            conexion.commit()
            return cursor.rowcount
    finally:
        conexion.close()


def _resumen_desde_periodos(cursor, fecha_inicio=None, fecha_fin=None):
    """Resumen de nómina a partir de los periodos liquidados (modelo nuevo)."""
    sql = """
        SELECT
            COALESCE(SUM(total_devengado), 0) AS total_devengado,
            COALESCE(SUM(total_deducciones), 0) AS total_deducciones,
            COALESCE(SUM(total_aportes + total_provisiones), 0) AS costo_patronal
        FROM nomina_periodos
        WHERE estado IN ('CALCULADO','CONTABILIZADO','PAGADO')
    """
    params = []
    if fecha_inicio:
        sql += " AND fecha_fin >= %s"
        params.append(fecha_inicio)
    if fecha_fin:
        sql += " AND fecha_inicio <= %s"
        params.append(fecha_fin)
    cursor.execute(sql, params)
    return cursor.fetchone()


def _resumen_legado(cursor, fecha_inicio=None, fecha_fin=None):
    """Resumen de nómina del modelo anterior (tabla ``nomina``).

    Se conserva como respaldo para instalaciones que todavía no han liquidado
    periodos con el motor nuevo.
    """
    sql = """
        SELECT
            COALESCE(SUM(salario_base), 0) AS total_devengado,
            COALESCE(SUM(total_deducciones), 0) AS total_deducciones,
            COALESCE(SUM(total_aportes), 0) AS costo_patronal
        FROM nomina
        WHERE 1 = 1
    """
    params = []
    if fecha_inicio and fecha_fin:
        sql += " AND STR_TO_DATE(CONCAT(periodo, '-01'), '%%Y-%%m-%%d') BETWEEN %s AND %s"
        params.extend([fecha_inicio, fecha_fin])
    cursor.execute(sql, params)
    return cursor.fetchone()


def obtener_resumen_nomina(fecha_inicio=None, fecha_fin=None):
    """Retorna la suma total de devengados, deducciones y costos patronales.

    Da prioridad a los periodos liquidados con el motor nuevo
    (``nomina_periodos``). Si aún no existen, usa el historial anterior
    (``nomina``) como respaldo. Ya no depende de ``pagos_nomina``, que el
    cálculo anterior nunca llenaba.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            try:
                resultado = _resumen_desde_periodos(cursor, fecha_inicio, fecha_fin)
                if resultado and float(resultado['total_devengado'] or 0) > 0:
                    origen = 'periodos'
                else:
                    resultado = _resumen_legado(cursor, fecha_inicio, fecha_fin)
                    origen = 'legado'
            except Exception:
                # La tabla nueva puede no existir en una base antigua.
                resultado = _resumen_legado(cursor, fecha_inicio, fecha_fin)
                origen = 'legado'

            total_devengado = float(resultado['total_devengado'] or 0)
            total_deducciones = float(resultado['total_deducciones'] or 0)
            costo_patronal = float(resultado['costo_patronal'] or 0)
            return {
                'costo_nomina': total_devengado + costo_patronal,
                'deducciones': total_deducciones,
                'total_devengado': total_devengado,
                'costo_patronal': costo_patronal,
                'origen': origen,
            }
    finally:
        conexion.close()


# ---------------------------------------------------------------
# Enlace con la aplicación (creación de tablas)
# ---------------------------------------------------------------

def crear_tablas_nomina():
    """Crea las tablas del módulo de nómina si no existen (no toca las demás)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS empleados (
                    id_empleado    INT AUTO_INCREMENT PRIMARY KEY,
                    nombres        VARCHAR(100) NOT NULL,
                    apellidos      VARCHAR(100) NOT NULL,
                    documento      VARCHAR(30)  NOT NULL UNIQUE,
                    cargo          VARCHAR(100),
                    salario_base   DECIMAL(12,2) NOT NULL,
                    fecha_ingreso  DATE NOT NULL,
                    estado         ENUM('ACTIVO','INACTIVO') NOT NULL DEFAULT 'ACTIVO',
                    creado_en      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS deducciones (
                    id_deduccion   INT AUTO_INCREMENT PRIMARY KEY,
                    nombre         VARCHAR(100) NOT NULL,
                    porcentaje     DECIMAL(6,3) NOT NULL,
                    activo         TINYINT(1)   NOT NULL DEFAULT 1
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS aportes (
                    id_aporte      INT AUTO_INCREMENT PRIMARY KEY,
                    nombre         VARCHAR(100) NOT NULL,
                    porcentaje     DECIMAL(6,3) NOT NULL,
                    activo         TINYINT(1)   NOT NULL DEFAULT 1
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS nomina (
                    id_nomina           INT AUTO_INCREMENT PRIMARY KEY,
                    id_empleado         INT NOT NULL,
                    periodo             VARCHAR(7) NOT NULL,
                    salario_base        DECIMAL(12,2) NOT NULL,
                    total_deducciones   DECIMAL(12,2) NOT NULL,
                    total_aportes       DECIMAL(12,2) NOT NULL,
                    salario_neto        DECIMAL(12,2) NOT NULL,
                    generado_en         TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_nomina_empleado FOREIGN KEY (id_empleado)
                        REFERENCES empleados(id_empleado)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS novedades (
                    id_novedad     INT AUTO_INCREMENT PRIMARY KEY,
                    id_empleado    INT NOT NULL,
                    tipo           ENUM('AUSENCIA','VACACIONES','PERMISO') NOT NULL,
                    fecha_inicio   DATE NOT NULL,
                    fecha_fin      DATE NOT NULL,
                    motivo         VARCHAR(255),
                    estado         ENUM('PENDIENTE','APROBADA','RECHAZADA')
                                   NOT NULL DEFAULT 'PENDIENTE',
                    creado_en      TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    CONSTRAINT fk_novedad_empleado FOREIGN KEY (id_empleado)
                        REFERENCES empleados(id_empleado)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )

            cursor.execute("SELECT COUNT(*) AS total FROM deducciones")
            if cursor.fetchone()["total"] == 0:
                cursor.executemany(
                    "INSERT INTO deducciones (nombre, porcentaje) VALUES (%s, %s)",
                    [("Salud (empleado)", 4.000), ("Pensión (empleado)", 4.000)],
                )

            cursor.execute("SELECT COUNT(*) AS total FROM aportes")
            if cursor.fetchone()["total"] == 0:
                cursor.executemany(
                    "INSERT INTO aportes (nombre, porcentaje) VALUES (%s, %s)",
                    [("Salud (empleador)", 8.500), ("Pensión (empleador)", 12.000), ("ARL", 0.522)],
                )

            # No se crean empleados de ejemplo: el motor de nómina solo debe
            # liquidar personas reales registradas por el usuario.

        conexion.commit()
    finally:
        conexion.close()
