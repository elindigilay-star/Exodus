"""Prepara la base de datos única de EXODUS Contable.

La estructura completa vive en `sistema_contable.sql` (una sola fuente de
verdad). Al arrancar, la aplicación:

  1. crea la base si no existe,
  2. aplica el esquema (es idempotente: no borra datos),
  3. agrega columnas nuevas a bases creadas con versiones anteriores,
  4. crea usuarios de demostración solo si la tabla está vacía y
     EXODUS_DEMO no es "0".
"""

import csv
import os
import re

import pymysql
from werkzeug.security import generate_password_hash

from config import DB_CONFIG, DB_NAME, DEMO
from database.connection import obtener_conexion

RUTA_ESQUEMA = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "..", "sistema_contable.sql"
)
RUTA_PUC = os.path.join(
    os.path.dirname(os.path.abspath(__file__)), "puc_colombia.csv"
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

    columnas_empleados = _columnas(cursor, "empleados")
    columnas_nuevas_empleados = (
        ("tipo_documento", "VARCHAR(10) NOT NULL DEFAULT 'CC' AFTER documento"),
        ("email", "VARCHAR(120) NULL AFTER cargo"),
        ("telefono", "VARCHAR(30) NULL AFTER email"),
        ("direccion", "VARCHAR(200) NULL AFTER telefono"),
        ("ciudad", "VARCHAR(80) NULL AFTER direccion"),
        ("fecha_nacimiento", "DATE NULL AFTER ciudad"),
        ("sexo", "ENUM('M','F','OTRO') NULL AFTER fecha_nacimiento"),
        ("estado_civil", "VARCHAR(30) NULL AFTER sexo"),
        ("tipo_contrato", "ENUM('INDEFINIDO','FIJO','OBRA_LABOR','APRENDIZAJE','PRESTACION_SERVICIOS') NOT NULL DEFAULT 'INDEFINIDO' AFTER estado_civil"),
        ("fecha_retiro", "DATE NULL AFTER fecha_ingreso"),
        ("salario_integral", "TINYINT(1) NOT NULL DEFAULT 0 AFTER salario_base"),
        ("auxilio_transporte", "DECIMAL(12,2) NULL AFTER salario_integral"),
        ("riesgo_arl", "TINYINT(4) NOT NULL DEFAULT 1 AFTER auxilio_transporte"),
        ("exonerado_salud", "TINYINT(1) NOT NULL DEFAULT 0 AFTER riesgo_arl"),
        ("exonerado_parafiscales", "TINYINT(1) NOT NULL DEFAULT 0 AFTER exonerado_salud"),
        ("centro_costo", "VARCHAR(80) NULL AFTER exonerado_parafiscales"),
        ("banco", "VARCHAR(80) NULL AFTER centro_costo"),
        ("cuenta_banco", "VARCHAR(50) NULL AFTER banco"),
        ("dependientes", "INT(11) NOT NULL DEFAULT 0 AFTER cuenta_banco"),
    )
    for columna, definicion in columnas_nuevas_empleados:
        if columna not in columnas_empleados:
            cursor.execute(f"ALTER TABLE empleados ADD COLUMN {columna} {definicion}")


def _cargar_puc(cursor):
    """Carga o actualiza el Plan Único de Cuentas desde el CSV del proyecto.

    Es idempotente: la clave única es el código de la cuenta. Si el CSV no
    existe (por ejemplo, una instalación mínima), el sistema sigue funcionando
    y el catálogo puede crearse manualmente.
    """
    if not os.path.exists(RUTA_PUC):
        return

    filas = []
    with open(RUTA_PUC, encoding="utf-8", newline="") as archivo:
        for fila in csv.DictReader(archivo):
            codigo = (fila.get("codigo") or "").strip()
            nombre = " ".join((fila.get("nombre") or "").split())
            if not codigo or not nombre:
                continue
            try:
                nivel = int(fila.get("nivel") or len(codigo))
                es_movimiento = int(fila.get("es_movimiento") or 1)
            except ValueError:
                nivel = len(codigo)
                es_movimiento = 1
            grupo = " ".join((fila.get("grupo") or "").split()) or None
            clase = (fila.get("clase") or codigo[:1]).strip()[:1] or "9"
            naturaleza = (fila.get("naturaleza") or "DEBITO").strip().upper()
            if naturaleza not in ("DEBITO", "CREDITO"):
                naturaleza = "DEBITO"
            filas.append((codigo, nombre, nivel, clase, grupo, naturaleza, es_movimiento))

    if not filas:
        return

    cursor.executemany(
        """
        INSERT INTO puc_cuentas
            (codigo, nombre, nivel, clase, grupo, naturaleza, es_movimiento)
        VALUES (%s, %s, %s, %s, %s, %s, %s)
        ON DUPLICATE KEY UPDATE
            nombre = VALUES(nombre),
            nivel = VALUES(nivel),
            clase = VALUES(clase),
            grupo = VALUES(grupo),
            naturaleza = VALUES(naturaleza),
            es_movimiento = VALUES(es_movimiento)
        """,
        filas,
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
            _cargar_puc(cursor)
            _crear_usuarios_demo(cursor)
        conexion.commit()
    finally:
        conexion.close()
