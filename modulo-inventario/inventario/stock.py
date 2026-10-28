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



def _etiquetas_disponibles(cursor):
    """True si la tabla `etiquetas` (de Configuración) ya existe en la base."""
    cursor.execute(
        """
        SELECT COUNT(*) AS n
          FROM information_schema.TABLES
         WHERE TABLE_SCHEMA = DATABASE() AND TABLE_NAME = 'etiquetas'
        """
    )
    return cursor.fetchone()['n'] > 0


def _validar_etiqueta(cursor, id_etiqueta):
    """Comprueba que la etiqueta exista y sea de tipo "producto". Devuelve su nombre."""
    if id_etiqueta is None:
        raise ErrorInventario('Selecciona la clasificación (etiqueta) del producto.')
    if not _etiquetas_disponibles(cursor):
        raise ErrorInventario(
            'Primero crea etiquetas de tipo Producto en Configuración → Etiquetas.', 409)
    cursor.execute(
        "SELECT nombre FROM etiquetas WHERE id = %s AND tipo = 'producto'", (id_etiqueta,))
    fila = cursor.fetchone()
    if fila is None:
        raise ErrorInventario('La clasificación elegida no existe o no es de tipo Producto.')
    return fila['nombre']


def listar_etiquetas_producto():
    """Etiquetas de tipo "producto" definidas en Configuración."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            if not _etiquetas_disponibles(cursor):
                return []
            cursor.execute(
                """
                SELECT id, nombre, porcentaje
                  FROM etiquetas
                 WHERE tipo = 'producto'
                 ORDER BY nombre
                """
            )
            return cursor.fetchall()
    finally:
        conexion.close()


def _vincular_categorias_existentes(cursor):
    """
    Productos antiguos que tenían la categoría escrita a mano: si el texto
    coincide con el nombre de una etiqueta de tipo producto, se vinculan solos.
    Es seguro repetirlo (solo toca productos sin etiqueta).
    """
    try:
        if not _etiquetas_disponibles(cursor):
            return
        cursor.execute(
            """
            UPDATE productos p
              JOIN etiquetas e ON e.tipo = 'producto' AND LOWER(e.nombre) = LOWER(p.categoria)
               SET p.id_etiqueta = e.id
             WHERE p.id_etiqueta IS NULL AND p.categoria IS NOT NULL
            """
        )
    except pymysql.MySQLError as error:
        print(f"AVISO: no se pudieron vincular las categorías antiguas a etiquetas: {error}")


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
                    id_etiqueta     INT NULL,
                    unidad          VARCHAR(20)  NOT NULL DEFAULT 'und',
                    costo_promedio  DECIMAL(12,2) NOT NULL DEFAULT 0,
                    precio_venta    DECIMAL(12,2) NOT NULL DEFAULT 0,
                    stock_actual    INT NOT NULL DEFAULT 0,
                    stock_minimo    INT NOT NULL DEFAULT 0,
                    activo          TINYINT(1) NOT NULL DEFAULT 1,
                    creado_en       TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
                    KEY idx_producto_etiqueta (id_etiqueta)
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


            cursor.execute(
                """
                SELECT COUNT(*) AS n
                  FROM information_schema.COLUMNS
                 WHERE TABLE_SCHEMA = DATABASE()
                   AND TABLE_NAME = 'productos' AND COLUMN_NAME = 'id_etiqueta'
                """
            )
            if cursor.fetchone()['n'] == 0:
                cursor.execute(
                    "ALTER TABLE productos "
                    "ADD COLUMN id_etiqueta INT NULL AFTER categoria, "
                    "ADD KEY idx_producto_etiqueta (id_etiqueta)"
                )

            _vincular_categorias_existentes(cursor)
 main
        conexion.commit()
    finally:
        conexion.close()





def _select_productos(cursor):
    """
    SELECT base de productos con su etiqueta. Devuelve (sql, con_etiquetas).
    Si Configuración aún no creó la tabla `etiquetas`, se consulta sin ella.
    """
    if _etiquetas_disponibles(cursor):
        return (
            "SELECT p.*, e.nombre AS etiqueta, e.porcentaje AS etiqueta_porcentaje "
            "FROM productos p "
            "LEFT JOIN etiquetas e ON e.id = p.id_etiqueta AND e.tipo = 'producto'",
            True,
        )
    return (
        "SELECT p.*, NULL AS etiqueta, NULL AS etiqueta_porcentaje FROM productos p",
        False,
    )


def listar_productos(buscar=None, estado=None, bajo_stock=False,
                     id_etiqueta=None, sin_clasificar=False):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql, con_etiquetas = _select_productos(cursor)
            sql += " WHERE 1=1"
            params = []
            if buscar:
                patron = f"%{buscar}%"
                if con_etiquetas:
                    sql += " AND (p.codigo LIKE %s OR p.nombre LIKE %s OR p.categoria LIKE %s OR e.nombre LIKE %s)"
                    params.extend([patron, patron, patron, patron])
                else:
                    sql += " AND (p.codigo LIKE %s OR p.nombre LIKE %s OR p.categoria LIKE %s)"
                    params.extend([patron, patron, patron])
            if estado == 'ACTIVO':
                sql += " AND p.activo = 1"
            elif estado == 'INACTIVO':
                sql += " AND p.activo = 0"
            if bajo_stock:
                sql += " AND p.activo = 1 AND p.stock_actual <= p.stock_minimo"
            if id_etiqueta:
                sql += " AND p.id_etiqueta = %s"
                params.append(id_etiqueta)
            elif sin_clasificar:
                sql += " AND e.id IS NULL" if con_etiquetas else " AND p.id_etiqueta IS NULL"
            sql += " ORDER BY p.activo DESC, p.nombre ASC"

            cursor.execute(sql, params)
            return cursor.fetchall()
    finally:
        conexion.close()


def obtener_producto(id_producto):
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            sql, _ = _select_productos(cursor)
            cursor.execute(sql + " WHERE p.id_producto = %s", (id_producto,))
            return cursor.fetchone()
    finally:
        conexion.close()


def _codigo_en_uso(cursor, codigo, excepto_id=None):
    cursor.execute(
        "SELECT id_producto FROM productos WHERE codigo = %s AND id_producto <> %s",
        (codigo, excepto_id or 0),
    )
    return cursor.fetchone() is not None


def crear_producto(codigo, nombre, descripcion, id_etiqueta, unidad, costo, precio_venta,
                   stock_inicial, stock_minimo, id_usuario=None):
    """Crea el producto; si hay stock inicial lo registra como una ENTRADA."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            _validar_etiqueta(cursor, id_etiqueta)
            if _codigo_en_uso(cursor, codigo):
                raise ErrorInventario('Ya existe un producto con ese código.', 409)
            try:
                cursor.execute(
                    """
                    INSERT INTO productos
                        (codigo, nombre, descripcion, id_etiqueta, unidad,
                         costo_promedio, precio_venta, stock_actual, stock_minimo)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
                    """,
                    (codigo, nombre, descripcion, id_etiqueta, unidad,
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


def actualizar_producto(id_producto, codigo, nombre, descripcion, id_etiqueta, unidad,
                        precio_venta, stock_minimo):
    """Edita los datos del producto. El stock y el costo solo cambian con movimientos."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_producto FROM productos WHERE id_producto = %s", (id_producto,))
            if cursor.fetchone() is None:
                raise ErrorInventario('El producto no existe.', 404)
            _validar_etiqueta(cursor, id_etiqueta)
            if _codigo_en_uso(cursor, codigo, id_producto):
                raise ErrorInventario('Ya existe otro producto con ese código.', 409)
            cursor.execute(
                """
                UPDATE productos
                   SET codigo = %s, nombre = %s, descripcion = %s, id_etiqueta = %s,
                       unidad = %s, precio_venta = %s, stock_minimo = %s
                 WHERE id_producto = %s
                """,
                (codigo, nombre, descripcion, id_etiqueta, unidad,
                 _dinero(precio_venta), stock_minimo, id_producto),
            )
        conexion.commit()
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def clasificar_producto(id_producto, id_etiqueta):
    """RF-04: asigna o cambia la clasificación (etiqueta) de un producto. Devuelve el nombre."""
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute("SELECT id_producto FROM productos WHERE id_producto = %s", (id_producto,))
            if cursor.fetchone() is None:
                raise ErrorInventario('El producto no existe.', 404)
            nombre_etiqueta = _validar_etiqueta(cursor, id_etiqueta)
            cursor.execute(
                "UPDATE productos SET id_etiqueta = %s WHERE id_producto = %s",
                (id_etiqueta, id_producto),
            )
        conexion.commit()
        return nombre_etiqueta
    except Exception:
        conexion.rollback()
        raise
    finally:
        conexion.close()


def eliminar_producto(id_producto):
    """
    RF-05: elimina un producto. Si ya tiene movimientos, el sistema lo impide.
    La entrada automática "Stock inicial" (creada al registrar el producto)
    no cuenta como movimiento: se borra junto con el producto.
    """
    conexion = obtener_conexion()
    try:
        with conexion.cursor() as cursor:
            cursor.execute(
                "SELECT id_producto FROM productos WHERE id_producto = %s FOR UPDATE", (id_producto,))
            if cursor.fetchone() is None:
                raise ErrorInventario('El producto no existe.', 404)
            cursor.execute(
                """
                SELECT COUNT(*) AS n
                  FROM movimientos_inventario
                 WHERE id_producto = %s
                   AND NOT (tipo = 'ENTRADA' AND motivo = 'Stock inicial')
                """,
                (id_producto,),
            )
            if cursor.fetchone()['n'] > 0:
                raise ErrorInventario(
                    'No se puede eliminar: el producto ya tiene movimientos registrados.', 409)
            cursor.execute("DELETE FROM movimientos_inventario WHERE id_producto = %s", (id_producto,))
            cursor.execute("DELETE FROM productos WHERE id_producto = %s", (id_producto,))
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

            if _etiquetas_disponibles(cursor):
                huerfano = (
                    "NOT EXISTS (SELECT 1 FROM etiquetas e "
                    "WHERE e.id = p.id_etiqueta AND e.tipo = 'producto')"
                )
            else:
                huerfano = "p.id_etiqueta IS NULL"
            cursor.execute(
                f"""
                SELECT COUNT(*)                                          AS productos_activos,
                       COALESCE(SUM(p.stock_actual), 0)                  AS unidades,
                       COALESCE(SUM(p.stock_actual * p.costo_promedio), 0) AS valor_costo,
                       COALESCE(SUM(p.stock_actual * p.precio_venta), 0)   AS valor_venta,
                       COALESCE(SUM(p.stock_actual <= p.stock_minimo), 0)  AS bajo_stock,
                       COALESCE(SUM(p.stock_actual = 0), 0)              AS agotados,
                       COALESCE(SUM({huerfano}), 0)                      AS sin_clasificar
                  FROM productos p
                 WHERE p.activo = 1
                """
            )
            return cursor.fetchone()
    finally:
        conexion.close()