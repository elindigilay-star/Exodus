from decimal import ROUND_HALF_UP, Decimal

import pymysql

from database.connection import obtener_conexion

TIPOS_MOVIMIENTO = ('ENTRADA', 'VENTA', 'SALIDA', 'AJUSTE')
DOS_DECIMALES = Decimal('0.01')


class ErrorInventario(ValueError):
    """Error de regla de negocio. `codigo` es el estado HTTP sugerido."""

    def __init__(self, mensaje, codigo=422):
        super().__init__(mensaje)
        self.codigo = codigo


def _dinero(valor):
    return Decimal(valor).quantize(DOS_DECIMALES, rounding=ROUND_HALF_UP)


def crear_tablas_inventario():
    """Crea las tablas del inventario si no existen (no toca las demás)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS productos (
                    id_producto     INT AUTO_INCREMENT PRIMARY KEY,
                    codigo          VARCHAR(40)  NOT NULL UNIQUE,
                    nombre          VARCHAR(150) NOT NULL,
                    descripcion     VARCHAR(255) NULL,
                    categoria       VARCHAR(80)  NULL,
                    unidad          VARCHAR(20)  NOT NULL DEFAULT 'und',
                    costo_promedio  DECIMAL(12,2) NOT NULL DEFAULT 0,
                    precio_venta    DECIMAL(12,2) NOT NULL DEFAULT 0,
                    stock_actual    INT NOT NULL DEFAULT 0,
                    stock_minimo    INT NOT NULL DEFAULT 0,
                    activo          TINYINT(1) NOT NULL DEFAULT 1,
                    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS movimientos_inventario (
                    id_movimiento    INT AUTO_INCREMENT PRIMARY KEY,
                    id_producto      INT NOT NULL,
                    tipo             ENUM('ENTRADA','VENTA','SALIDA','AJUSTE') NOT NULL,
                    cantidad         INT NOT NULL,
                    stock_resultante INT NOT NULL,
                    costo_unitario   DECIMAL(12,2) NOT NULL DEFAULT 0,
                    precio_unitario  DECIMAL(12,2) NULL,
                    motivo           VARCHAR(255) NULL,
                    id_venta         INT NULL,
                    id_usuario       INT NULL,
                    fecha            DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_mov_producto (id_producto),
                    KEY idx_mov_fecha (fecha),
                    CONSTRAINT fk_mov_producto FOREIGN KEY (id_producto)
                        REFERENCES productos(id_producto)
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS etiquetas (
                    id INT AUTO_INCREMENT PRIMARY KEY,
                    nombre VARCHAR(80) NOT NULL UNIQUE,
                    tipo VARCHAR(20) NOT NULL,
                    porcentaje DECIMAL(5,2) NOT NULL DEFAULT 0
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        conexion.commit()
    finally:
        conexion.close()


def listar_productos(buscar=None, estado=None, bajo_stock=False):
    sql = "SELECT * FROM productos WHERE 1=1"
    params = []
    if buscar:
        sql += " AND (codigo LIKE %s OR nombre LIKE %s OR categoria LIKE %s)"
        patron = f"%{buscar}%"
        params.extend([patron, patron, patron])
    if estado == 'ACTIVO':
        sql += " AND activo = 1"
    elif estado == 'INACTIVO':
        sql += " AND activo = 0"
    if bajo_stock:
        sql += " AND activo = 1 AND stock_actual <= stock_minimo"
    sql += " ORDER BY activo DESC, nombre ASC"

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_producto(id_producto):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT * FROM productos WHERE id_producto = %s", (id_producto,))
            return cursor.fetchone()
    finally:
        conexion.close()


def _codigo_en_uso(cursor, codigo, excepto_id=None):
    cursor.execute(
        "SELECT id_producto FROM productos WHERE codigo = %s AND id_producto <> %s",
        (codigo, excepto_id or 0),
    )
    return cursor.fetchone() is not None


def crear_producto(codigo, nombre, descripcion, categoria, unidad, costo, precio_venta,
                   stock_inicial, stock_minimo, id_usuario=None):
    """Crea el producto; si hay stock inicial lo registra como una ENTRADA."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            if _codigo_en_uso(cursor, codigo):
                raise ErrorInventario('Ya existe un producto con ese código.', 409)
            try:
                cursor.execute(
                    """
                    INSERT INTO productos
                        (codigo, nombre, descripcion, categoria, unidad,
                         costo_promedio, precio_venta, stock_actual, stock_minimo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (codigo, nombre, descripcion, categoria, unidad,
                     _dinero(costo), _dinero(precio_venta), stock_inicial, stock_minimo),
                )
            except pymysql.err.IntegrityError:
                raise ErrorInventario('Ya existe un producto con ese código.', 409)
            id_producto = cursor.lastrowid
            if stock_inicial > 0:
                cursor.execute(
                    """
                    INSERT INTO movimientos_inventario
                        (id_producto, tipo, cantidad, stock_resultante, costo_unitario, motivo, id_usuario)
                    VALUES (%s, 'ENTRADA', %s, %s, %s, 'Stock inicial', %s)
                    """,
                    (id_producto, stock_inicial, stock_inicial, _dinero(costo), id_usuario),
                )
        conexion.commit()
        return id_producto
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def actualizar_producto(id_producto, codigo, nombre, descripcion, categoria, unidad,
                        precio_venta, stock_minimo):
    """Edita los datos del producto. El stock y el costo solo cambian con movimientos."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_producto FROM productos WHERE id_producto = %s", (id_producto,))
            if cursor.fetchone() is None:
                raise ErrorInventario('El producto no existe.', 404)
            if _codigo_en_uso(cursor, codigo, id_producto):
                raise ErrorInventario('Ya existe otro producto con ese código.', 409)
            cursor.execute(
                """
                UPDATE productos
                   SET codigo = %s, nombre = %s, descripcion = %s, categoria = %s,
                       unidad = %s, precio_venta = %s, stock_minimo = %s
                 WHERE id_producto = %s
                """,
                (codigo, nombre, descripcion, categoria, unidad,
                 _dinero(precio_venta), stock_minimo, id_producto),
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def cambiar_estado_producto(id_producto, activo):
    """Activa o desactiva (no se borra, para conservar el historial)."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_producto FROM productos WHERE id_producto = %s", (id_producto,))
            if cursor.fetchone() is None:
                raise ErrorInventario('El producto no existe.', 404)
            cursor.execute(
                "UPDATE productos SET activo = %s WHERE id_producto = %s",
                (1 if activo else 0, id_producto),
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def registrar_movimiento(id_producto, tipo, cantidad, costo_unitario=None,
                         precio_unitario=None, motivo=None, id_usuario=None):
    """
    Registra un movimiento y actualiza el stock en una sola transacción.

    - ENTRADA: compra/reposición. Recalcula el costo promedio ponderado.
    - VENTA:   sale stock y se registra en `ventas_inventario` (contabilidad).
    - SALIDA:  baja por daño, merma, consumo interno, etc. (no es venta).
    - AJUSTE:  `cantidad` es el conteo físico real; se guarda la diferencia.
    """
    if tipo not in TIPOS_MOVIMIENTO:
        raise ErrorInventario('Tipo de movimiento no válido.')
    if tipo == 'AJUSTE':
        if cantidad < 0:
            raise ErrorInventario('El conteo físico no puede ser negativo.')
    elif cantidad <= 0:
        raise ErrorInventario('La cantidad debe ser mayor a 0.')
    if tipo in ('SALIDA', 'AJUSTE') and not motivo:
        raise ErrorInventario('Escribe el motivo del movimiento.')

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            # Bloquea la fila para que dos movimientos simultáneos no pisen el stock.
            cursor.execute("SELECT * FROM productos WHERE id_producto = %s FOR UPDATE", (id_producto,))
            producto = cursor.fetchone()
            if producto is None:
                raise ErrorInventario('El producto no existe.', 404)
            if not producto['activo']:
                raise ErrorInventario('El producto está inactivo. Actívalo para registrar movimientos.', 409)

            stock = producto['stock_actual']
            costo_actual = Decimal(producto['costo_promedio'])
            nuevo_costo = costo_actual
            precio_registrado = None
            id_venta = None

            if tipo == 'ENTRADA':
                costo_entrada = _dinero(costo_unitario if costo_unitario is not None else costo_actual)
                delta = cantidad
                nuevo_stock = stock + delta
                nuevo_costo = _dinero(
                    (Decimal(stock) * costo_actual + Decimal(delta) * costo_entrada) / Decimal(nuevo_stock)
                )
                costo_movimiento = costo_entrada
            elif tipo == 'AJUSTE':
                delta = cantidad - stock
                if delta == 0:
                    raise ErrorInventario('El conteo coincide con el stock actual; no hay nada que ajustar.')
                nuevo_stock = cantidad
                costo_movimiento = costo_actual
            else:  # VENTA o SALIDA
                if cantidad > stock:
                    raise ErrorInventario(f'Stock insuficiente: hay {stock} y se piden {cantidad}.', 409)
                delta = -cantidad
                nuevo_stock = stock + delta
                costo_movimiento = costo_actual
                if tipo == 'VENTA':
                    precio_registrado = _dinero(
                        precio_unitario if precio_unitario is not None else producto['precio_venta']
                    )
                    # Alimenta contabilidad (Estado de Resultados) con la tabla existente.
                    cursor.execute(
                        "INSERT INTO ventas_inventario (monto_total, costo_ventas) VALUES (%s, %s)",
                        (precio_registrado * cantidad, costo_actual * cantidad),
                    )
                    id_venta = cursor.lastrowid

            cursor.execute(
                "UPDATE productos SET stock_actual = %s, costo_promedio = %s WHERE id_producto = %s",
                (nuevo_stock, nuevo_costo, id_producto),
            )
            cursor.execute(
                """
                INSERT INTO movimientos_inventario
                    (id_producto, tipo, cantidad, stock_resultante, costo_unitario,
                     precio_unitario, motivo, id_venta, id_usuario)
                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                """,
                (id_producto, tipo, delta, nuevo_stock, costo_movimiento,
                 precio_registrado, motivo, id_venta, id_usuario),
            )
            id_movimiento = cursor.lastrowid
        conexion.commit()
        return {
            'id_movimiento': id_movimiento,
            'id_venta': id_venta,
            'stock_resultante': nuevo_stock,
            'costo_promedio': float(nuevo_costo),
        }
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def listar_movimientos(id_producto=None, limite=100):
    sql = """
        SELECT m.*, p.codigo, p.nombre AS producto, u.nombre AS usuario
          FROM movimientos_inventario m
          JOIN productos p ON p.id_producto = m.id_producto
          LEFT JOIN usuarios u ON u.id_usuario = m.id_usuario
    """
    params = []
    if id_producto:
        sql += " WHERE m.id_producto = %s"
        params.append(id_producto)
    sql += " ORDER BY m.fecha DESC, m.id_movimiento DESC LIMIT %s"
    params.append(limite)

    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_resumen_stock():
    """Indicadores para el encabezado del módulo."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                """
                SELECT COUNT(*)                                        AS productos_activos,
                       COALESCE(SUM(stock_actual), 0)                  AS unidades,
                       COALESCE(SUM(stock_actual * costo_promedio), 0) AS valor_costo,
                       COALESCE(SUM(stock_actual * precio_venta), 0)   AS valor_venta,
                       COALESCE(SUM(stock_actual <= stock_minimo), 0)  AS bajo_stock,
                       COALESCE(SUM(stock_actual = 0), 0)              AS agotados
                  FROM productos
                 WHERE activo = 1
                """
            )
            return cursor.fetchone()
    finally:
        conexion.close()