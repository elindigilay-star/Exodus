"""Rutas (API) del módulo de inventario de EXODUS Contable.

Vive en `modulo-inventario/inventario/rutas.py` y se registra en la app
principal desde `Modulo-contable/app.py` con `registrar_inventario(app)`.

- La lógica de datos está en `stock.py` (productos y movimientos).
- La plantilla está en `templates/inventario/modulo.html`.
- El CSS y el JavaScript están en `static/`.
"""

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from functools import wraps

import pymysql
from flask import Blueprint, jsonify, render_template, request, session


from . import stock as modelo

from routes.auth import login_requerido

inventario_modulo_bp = Blueprint(
    'inventario_modulo', __name__,
    template_folder='templates',
    static_folder='static',
)


ROLES_ESCRITURA = ('Administrador', 'Contador', 'Auxiliar')


def _rol_en(roles_permitidos):
    """Compara el rol de la sesión sin importar mayúsculas/minúsculas."""
    rol = (session.get('usuario_rol') or '').strip().lower()
    return rol in {r.lower() for r in roles_permitidos}


def acceso_api(*roles):
    """Como login_requerido, pero responde JSON (401/403) en lugar de redirigir."""
    def decorador(f):
        @wraps(f)
        def interno(*args, **kwargs):
            if not session.get('usuario_id'):
                return jsonify({'error': 'Tu sesión expiró. Inicia sesión de nuevo.'}), 401
            if roles and not _rol_en(roles):
                return jsonify({'error': 'Tu rol no tiene permiso para modificar el inventario.'}), 403
            return f(*args, **kwargs)
        return interno
    return decorador


def _datos_json():
    datos = request.get_json(silent=True)
    return datos if isinstance(datos, dict) else {}


def _texto(valor, maximo):
    texto = ('' if valor is None else str(valor)).strip()
    if len(texto) > maximo:
        raise modelo.ErrorInventario(f'Un texto supera los {maximo} caracteres permitidos.')
    return texto or None


def _entero(valor, nombre, minimo=0, obligatorio=False):
    if valor in (None, ''):
        if obligatorio:
            raise modelo.ErrorInventario(f'Falta {nombre}.')
        return minimo if minimo > 0 else 0
    try:
        numero = Decimal(str(valor))
    except InvalidOperation:
        raise modelo.ErrorInventario(f'{nombre.capitalize()} debe ser un número entero.')
    if numero != numero.to_integral_value():
        raise modelo.ErrorInventario(f'{nombre.capitalize()} debe ser un número entero.')
    numero = int(numero)
    if numero < minimo:
        raise modelo.ErrorInventario(f'{nombre.capitalize()} no puede ser menor a {minimo}.')
    return numero


def _dinero(valor, nombre, obligatorio=True):
    if valor in (None, ''):
        if obligatorio:
            raise modelo.ErrorInventario(f'Falta {nombre}.')
        return None
    try:
        numero = Decimal(str(valor))
    except InvalidOperation:
        raise modelo.ErrorInventario(f'{nombre.capitalize()} debe ser un número.')
    if not numero.is_finite() or numero < 0:
        raise modelo.ErrorInventario(f'{nombre.capitalize()} no puede ser negativo.')
    return numero


def _normalizar(fila):
    salida = {}
    for clave, valor in fila.items():
        if isinstance(valor, Decimal):
            salida[clave] = float(valor)
        elif isinstance(valor, datetime):
            salida[clave] = valor.strftime('%Y-%m-%d %H:%M:%S')
        elif isinstance(valor, date):
            salida[clave] = valor.strftime('%Y-%m-%d')
        else:
            salida[clave] = valor
    return salida


def _normalizar_lista(filas):
    return [_normalizar(f) for f in filas]


def _campos_producto(datos):
    codigo = _texto(datos.get('codigo'), 40)
    nombre = _texto(datos.get('nombre'), 150)
    if not codigo or not nombre:
        raise modelo.ErrorInventario('El código y el nombre son obligatorios.')
    return {
        'codigo': codigo.upper(),
        'nombre': nombre,
        'descripcion': _texto(datos.get('descripcion'), 255),
        'categoria': _texto(datos.get('categoria'), 80),
        'unidad': _texto(datos.get('unidad'), 20) or 'und',
        'precio_venta': _dinero(datos.get('precio_venta'), 'el precio de venta'),
        'stock_minimo': _entero(datos.get('stock_minimo'), 'el stock mínimo'),
    }


# Errores siempre en JSON para que el JavaScript los muestre
@inventario_modulo_bp.errorhandler(modelo.ErrorInventario)
def _error_negocio(error):
    return jsonify({'error': str(error)}), error.codigo


@inventario_modulo_bp.errorhandler(pymysql.MySQLError)
def _error_bd(_error):
    return jsonify({'error': 'No se pudo completar la operación en la base de datos.'}), 500




@inventario_modulo_bp.route('/modulo', methods=['GET'])
@login_requerido
def modulo():
    return render_template(
        'inventario/modulo.html',
        puede_editar=_rol_en(ROLES_ESCRITURA),
    )




@inventario_modulo_bp.route('/resumen', methods=['GET'])
@acceso_api()
def api_resumen():
    return jsonify(_normalizar(modelo.obtener_resumen_stock())), 200


@inventario_modulo_bp.route('/productos', methods=['GET'])
@acceso_api()
def api_listar_productos():
    estado = (request.args.get('estado') or '').upper() or None
    productos = modelo.listar_productos(
        buscar=(request.args.get('buscar') or '').strip() or None,
        estado=estado,
        bajo_stock=request.args.get('bajo_stock') == '1',
    )
    return jsonify(_normalizar_lista(productos)), 200


@inventario_modulo_bp.route('/productos', methods=['POST'])
@acceso_api(*ROLES_ESCRITURA)
def api_crear_producto():
    datos = _datos_json()
    campos = _campos_producto(datos)
    costo = _dinero(datos.get('costo'), 'el costo')
    stock_inicial = _entero(datos.get('stock_inicial'), 'el stock inicial')

    id_producto = modelo.crear_producto(
        campos['codigo'], campos['nombre'], campos['descripcion'], campos['categoria'],
        campos['unidad'], costo, campos['precio_venta'], stock_inicial,
        campos['stock_minimo'], session.get('usuario_id'),
    )
    return jsonify({'mensaje': 'Producto registrado correctamente.', 'id_producto': id_producto}), 201


@inventario_modulo_bp.route('/productos/actualizar', methods=['POST'])
@acceso_api(*ROLES_ESCRITURA)
def api_actualizar_producto():
    datos = _datos_json()
    id_producto = _entero(datos.get('id_producto'), 'el producto', minimo=1, obligatorio=True)
    campos = _campos_producto(datos)
    modelo.actualizar_producto(
        id_producto, campos['codigo'], campos['nombre'], campos['descripcion'],
        campos['categoria'], campos['unidad'], campos['precio_venta'], campos['stock_minimo'],
    )
    return jsonify({'mensaje': 'Producto actualizado correctamente.'}), 200


@inventario_modulo_bp.route('/productos/estado', methods=['POST'])
@acceso_api(*ROLES_ESCRITURA)
def api_estado_producto():
    datos = _datos_json()
    id_producto = _entero(datos.get('id_producto'), 'el producto', minimo=1, obligatorio=True)
    activo = datos.get('activo') in (True, 1, '1', 'true')
    modelo.cambiar_estado_producto(id_producto, activo)
    return jsonify({'mensaje': 'Producto activado.' if activo else 'Producto desactivado.'}), 200





@inventario_modulo_bp.route('/movimientos', methods=['GET'])
@acceso_api()
def api_listar_movimientos():
    try:
        id_producto = int(request.args.get('id_producto') or 0) or None
        limite = min(max(int(request.args.get('limite') or 100), 1), 500)
    except ValueError:
        return jsonify({'error': 'Parámetros no válidos.'}), 422
    return jsonify(_normalizar_lista(modelo.listar_movimientos(id_producto, limite))), 200


@inventario_modulo_bp.route('/movimientos', methods=['POST'])
@acceso_api(*ROLES_ESCRITURA)
def api_registrar_movimiento():
    datos = _datos_json()
    id_producto = _entero(datos.get('id_producto'), 'el producto', minimo=1, obligatorio=True)
    tipo = str(datos.get('tipo') or '').upper()
    cantidad = _entero(datos.get('cantidad'), 'la cantidad', obligatorio=True)

    resultado = modelo.registrar_movimiento(
        id_producto, tipo, cantidad,
        costo_unitario=_dinero(datos.get('costo_unitario'), 'el costo unitario', obligatorio=False),
        precio_unitario=_dinero(datos.get('precio_unitario'), 'el precio unitario', obligatorio=False),
        motivo=_texto(datos.get('motivo'), 255),
        id_usuario=session.get('usuario_id'),
    )
    return jsonify({'mensaje': 'Movimiento registrado correctamente.', **resultado}), 201




def registrar_inventario(app):
    """Registra el blueprint y prepara las tablas. Se llama una vez desde app.py.

    Se monta en /api/inventario:
      - vista:  /api/inventario/modulo
      - API:    /api/inventario/productos, /movimientos, /resumen, ...
      - static: /api/inventario/static/css/inventario.css, .../js/inventario.js
    """
    app.register_blueprint(inventario_modulo_bp, url_prefix='/api/inventario')
    try:
        modelo.crear_tablas_inventario()
    except Exception as error:  # La app arranca aunque la base de datos esté apagada
        print(f"AVISO: no se pudieron preparar las tablas de inventario: {error}")