"""Prepara la base de datos única de EXODUS Contable.

La estructura completa vive en `sistema_contable.sql` (una sola fuente de
verdad). Al arrancar, la aplicación:

  1. crea la base si no existe,
  2. aplica el esquema (es idempotente: no borra datos),
  3. agrega columnas nuevas a bases creadas con versiones anteriores,
  4. crea usuarios de demostración solo si la tabla está vacía y
     EXODUS_DEMO no es "0".
"""

import os
import re

import pymysql
from werkzeug.security import generate_password_hash

from config import DB_CONFIG, DB_NAME, DEMO
from database.connection import obtener_conexion

RUTA_ESQUEMA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "sistema_contable.sql"
)

CREDENCIALES_DEMO = {
    "carlos": ("carlos123", "Carlos Pérez", "Administrador"),
    "ana": ("ana123", "Ana Gómez", "Contador"),
    "juan": ("juan123", "Juan Torres", "Auxiliar"),
    "admin": ("admin123", "Administrador Principal", "Administrador"),
    "contador": ("contador123", "Contador Jefe", "Contador"),
    "auxiliar": ("auxiliar123", "Auxiliar Administrativo", "Auxiliar"),
}


def _leer_sentencias():
    """Lee el .sql y devuelve las sentencias sin comentarios."""
    with open(RUTA_ESQUEMA, encoding="utf-8") as archivo:
        lineas = [linea for linea in archivo if not linea.lstrip().startswith("--")]
    for bloque in "\n".join(lineas).split(";"):
        sentencia = bloque.strip()
        if sentencia:
            yield sentencia


def _crear_base_si_falta():
    """Crea la base de datos cuando todavía no existe."""
    if not re.fullmatch(r"[A-Za-z0-9_]+", DB_NAME):
        raise ValueError(f"Nombre de base de datos no válido: {DB_NAME!r}")

    conexion = pymysql.connect(
        host=DB_CONFIG["host"],
        port=DB_CONFIG["port"],
        user=DB_CONFIG["user"],
        password=DB_CONFIG["password"],
        charset=DB_CONFIG["charset"],
    )
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                f"CREATE DATABASE IF NOT EXISTS `{DB_NAME}` "
                "DEFAULT CHARACTER SET utf8mb4 COLLATE utf8mb4_general_ci"
            )
        conexion.commit()
    finally:
        conexion.close()


def _columnas(cursor, tabla):
    cursor.execute(
        """
        SELECT COLUMN_NAME
        FROM information_schema.COLUMNS
        WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = %s
        """,
        (tabla,),
    )
    return {fila["COLUMN_NAME"] for fila in cursor.fetchall()}


def _migrar_columnas(cursor):
    """Agrega columnas nuevas a bases creadas con versiones anteriores."""
    columnas_usuarios = _columnas(cursor, "usuarios")
    if "usuario" not in columnas_usuarios:
        cursor.execute(
            "ALTER TABLE usuarios ADD COLUMN usuario VARCHAR(50) NULL UNIQUE AFTER id_usuario"
        )
    if "clave_hash" not in columnas_usuarios:
        cursor.execute(
            "ALTER TABLE usuarios ADD COLUMN clave_hash VARCHAR(255) NULL AFTER email"
        )
    if "activo" not in columnas_usuarios:
        cursor.execute(
            "ALTER TABLE usuarios ADD COLUMN activo TINYINT(1) NOT NULL DEFAULT 1"
        )

    # El rol de nómina se agregó después de la primera versión del esquema.
    cursor.execute(
        "ALTER TABLE usuarios MODIFY COLUMN rol "
        "ENUM('Administrador','Contador','Auxiliar','Empleado','Recursos Humanos') "
        "NOT NULL DEFAULT 'Empleado'"
    )

    columnas_gastos = _columnas(cursor, "gastos_deducibles")
    for columna, definicion in (
        ("categoria", "VARCHAR(80) NULL AFTER descripcion"),
        ("tercero", "VARCHAR(150) NULL AFTER categoria"),
        ("nit", "VARCHAR(30) NULL AFTER tercero"),
        ("numero_documento", "VARCHAR(50) NULL AFTER nit"),
        ("estado_gasto", "ENUM('ACTIVO','ANULADO') NOT NULL DEFAULT 'ACTIVO' AFTER id_usuario"),
    ):
        if columna not in columnas_gastos:
            cursor.execute(f"ALTER TABLE gastos_deducibles ADD COLUMN {columna} {definicion}")

    columnas_productos = _columnas(cursor, "productos")
    if "id_etiqueta" not in columnas_productos:
        cursor.execute(
            "ALTER TABLE productos ADD COLUMN id_etiqueta INT NULL AFTER categoria, "
            "ADD KEY idx_producto_etiqueta (id_etiqueta)"
        )


def _crear_usuarios_demo(cursor):
    """Crea usuarios de prueba solo en una base vacía y si EXODUS_DEMO=1."""
    if not DEMO:
        return
    cursor.execute("SELECT COUNT(*) AS total FROM usuarios")
    if cursor.fetchone()["total"]:
        return

    demo = [
        (usuario, nombre, clave, rol)
        for usuario, (clave, nombre, rol) in CREDENCIALES_DEMO.items()
    ]
    cursor.executemany(
        """
        INSERT INTO usuarios (usuario, nombre, email, clave_hash, rol, activo)
        VALUES (%s, %s, %s, %s, %s, 1)
        """,
        [
            (usuario, nombre, f"{usuario}@exodo.local", generate_password_hash(clave), rol)
            for usuario, nombre, clave, rol in demo
        ],
    )
    print(
        "AVISO: se crearon usuarios de demostración (admin/admin123, ...). "
        "Cámbialos antes de usar el sistema en producción o define EXODUS_DEMO=0."
    )


def _seed_plan_cuentas(cursor):
    """Siembra el plan de cuentas base para PYMES colombianas si la tabla está vacía."""
    cursor.execute("SELECT COUNT(*) AS total FROM plan_cuentas")
    if cursor.fetchone()["total"] > 0:
        return

    cuentas = [
        # (codigo, nombre, tipo, naturaleza, cuenta_padre_codigo, nivel, permite_movimiento)
        ("1", "ACTIVO", "grupo", "ninguna", None, 1, 0),
        ("11", "ACTIVO CIRCULANTE", "grupo", "ninguna", "1", 2, 0),
        ("1105", "Caja", "cuenta", "deudora", "11", 3, 1),
        ("1110", "Bancos", "cuenta", "deudora", "11", 3, 1),
        ("1130", "Inventario de mercancías", "cuenta", "deudora", "11", 3, 1),
        ("1305", "Cuentas por cobrar clientes", "cuenta", "deudora", "11", 3, 1),
        ("12", "ACTIVO NO CIRCULANTE", "grupo", "ninguna", "1", 2, 0),
        ("1205", "Mobiliario y equipo", "cuenta", "deudora", "12", 3, 1),
        ("2", "PASIVO", "grupo", "ninguna", None, 1, 0),
        ("21", "PASIVO CIRCULANTE", "grupo", "ninguna", "2", 2, 0),
        ("2105", "Proveedores / Cuentas por pagar", "cuenta", "acreedora", "21", 3, 1),
        ("2110", "IVA por pagar", "cuenta", "acreedora", "21", 3, 1),
        ("2405", "Nómina por pagar", "cuenta", "acreedora", "21", 3, 1),
        ("2410", "Retenciones y aportes por pagar", "cuenta", "acreedora", "21", 3, 1),
        ("3", "PATRIMONIO", "grupo", "ninguna", None, 1, 0),
        ("3105", "Capital social", "cuenta", "acreedora", "3", 3, 1),
        ("3110", "Utilidades acumuladas", "cuenta", "acreedora", "3", 3, 1),
        ("4", "INGRESOS", "grupo", "ninguna", None, 1, 0),
        ("4105", "Ventas", "cuenta", "acreedora", "4", 3, 1),
        ("5", "COSTOS Y GASTOS", "grupo", "ninguna", None, 1, 0),
        ("5105", "Costo de ventas", "cuenta", "deudora", "5", 3, 1),
        ("5205", "Gastos de nómina", "cuenta", "deudora", "5", 3, 1),
        ("5210", "Gastos generales deducibles", "cuenta", "deudora", "5", 3, 1),
        ("5220", "Servicios públicos", "cuenta", "deudora", "5", 3, 1),
        ("5230", "Arriendos", "cuenta", "deudora", "5", 3, 1),
    ]

    # Insertar en orden de nivel para respetar claves foráneas autopreferenciadas
    for nivel in (1, 2, 3):
        for codigo, nombre, tipo, naturaleza, padre_codigo, lev, permite in cuentas:
            if lev != nivel:
                continue
            padre_id = None
            if padre_codigo:
                cursor.execute("SELECT id_cuenta FROM plan_cuentas WHERE codigo = %s", (padre_codigo,))
                fila = cursor.fetchone()
                if fila:
                    padre_id = fila["id_cuenta"]
            cursor.execute(
                """
                INSERT IGNORE INTO plan_cuentas
                    (codigo, nombre, tipo, naturaleza, cuenta_padre_id, nivel, permite_movimiento, activo)
                VALUES (%s, %s, %s, %s, %s, %s, %s, 1)
                """,
                (codigo, nombre, tipo, naturaleza, padre_id, lev, permite),
            )


def _seed_parametros_tributarios(cursor):
    """Siembra parámetros tributarios base (IVA colombiano) si la tabla está vacía."""
    cursor.execute("SELECT COUNT(*) AS total FROM parametros_tributarios")
    if cursor.fetchone()["total"] > 0:
        return

    from datetime import date
    parametros = [
        ("IVA general", 19.000, date(2020, 1, 1), None),
        ("IVA reducido", 5.000, date(2020, 1, 1), None),
        ("IVA excluido", 0.000, date(2020, 1, 1), None),
    ]
    cursor.executemany(
        """
        INSERT IGNORE INTO parametros_tributarios
            (nombre, valor, vigencia_desde, vigencia_hasta, activo)
        VALUES (%s, %s, %s, %s, 1)
        """,
        parametros,
    )


def crear_admin(usuario, clave, nombre="Administrador", email=None):
    """Crea (o actualiza la clave de) un usuario administrador."""
    from models.usuario import crear_usuario, existe_usuario  # import local: evita ciclos

    if existe_usuario(usuario):
        raise ValueError(f"El usuario {usuario!r} ya existe.")
    return crear_usuario(
        nombre=nombre,
        usuario=usuario,
        email=email or f"{usuario}@exodo.local",
        rol="Administrador",
        clave=clave,
        activo=True,
    )


def iniciar_db():
    """Crea/migra la base de datos y deja el sistema listo para iniciar sesión."""
    _crear_base_si_falta()

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            for sentencia in _leer_sentencias():
                cursor.execute(sentencia)
            _migrar_columnas(cursor)
            _seed_plan_cuentas(cursor)
            _seed_parametros_tributarios(cursor)
            _crear_usuarios_demo(cursor)
        conexion.commit()
    finally:
        conexion.close()
