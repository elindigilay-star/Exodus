import pymysql
from flask import (Blueprint, jsonify, render_template, request, send_file,
                   session)
from services.estado_resultados_service import generar_estado_resultados
from services.gasto_service import (
    registrar_gasto_deducible, listar_gastos_deducibles, obtener_gasto_deducible,
    editar_gasto_deducible, anular_gasto_deducible
)
from services.consolidacion_service import consolidar_informacion_contable
from services.balance_service import calcular_balance_general
from services.reporte_service import (
    exportar_estado_resultados_pdf, exportar_estado_resultados_excel,
    exportar_balance_general_pdf, exportar_balance_general_excel,
    exportar_consolidado_pdf, exportar_consolidado_excel,
    obtener_estado_resultados_con_periodo, obtener_balance_con_periodo,
    obtener_consolidado_con_periodo
)
from services.comprobante_service import (
    buscar_cuentas, crear_cuenta, crear_comprobante, listar_comprobantes,
    obtener_comprobante, anular_comprobante, libro_mayor, balance_prueba
)
from routes.auth import api_requerir_roles, requerir_roles

contabilidad_bp = Blueprint('contabilidad', __name__)


def fecha_a_texto(valor):
    """Convierte la fecha a texto sin importar si llega como str o como date/datetime."""
    if valor is None:
        return None
    if isinstance(valor, str):
        return valor  # ya es texto
    return valor.strftime('%Y-%m-%d %H:%M:%S')


# CU-01: Estado de Resultados
@contabilidad_bp.route('/estado-resultados', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_estado_resultados():
    """Devuelve el Estado de Resultados del periodo en JSON."""
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        resultado = generar_estado_resultados(f_inicio, f_fin)
        return jsonify({"estado": "exito", "data": resultado}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400

# CU-02: Registrar Gastos Deducibles (Restringido a Contador y Administrador)
@contabilidad_bp.route('/gastos', methods=['POST'])
@api_requerir_roles('Contador', 'Administrador')
def api_registrar_gasto():
    """Registra un gasto deducible desde la API."""
    try:
        datos = request.get_json() or {}
        id_usuario = session.get('usuario_id')
        respuesta = registrar_gasto_deducible(
            descripcion=datos.get('descripcion'),
            monto=datos.get('monto'),
            id_usuario=id_usuario,
            categoria=datos.get('categoria'),
            tercero=datos.get('tercero'),
            nit=datos.get('nit'),
            numero_documento=datos.get('numero_documento'),
            fecha=datos.get('fecha')
        )
        return jsonify({"estado": "exito", "data": respuesta}), 201
    except (ValueError, PermissionError) as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400

# CU-02b: Listar gastos deducibles
@contabilidad_bp.route('/gastos', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_listar_gastos():
    """Lista los gastos deducibles, opcionalmente por periodo."""
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        estado = request.args.get('estado', 'ACTIVO')
        gastos = listar_gastos_deducibles(
            fecha_inicio=f_inicio, fecha_fin=f_fin, estado_gasto=estado
        )
        # Convertir fechas a string para JSON serializable
        resultado = []
        for g in gastos:
            item = dict(g)
            item['fecha'] = fecha_a_texto(item.get('fecha'))
            resultado.append(item)
        return jsonify({"estado": "exito", "data": resultado}), 200
    except pymysql.MySQLError as error:
        print(f"AVISO: no se pudieron listar los gastos: {error}")
        return jsonify({
            "estado": "error",
            "mensaje": "No se pudo consultar la base de datos.",
        }), 500

# CU-02c: Obtener un gasto para editar
@contabilidad_bp.route('/gastos/<int:id_gasto>', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_obtener_gasto(id_gasto):
    """Devuelve un gasto deducible por su identificador."""
    try:
        gasto = obtener_gasto_deducible(id_gasto)
        if not gasto:
            return jsonify({"estado": "error", "mensaje": "Gasto no encontrado."}), 404
        item = dict(gasto)
        item['fecha'] = fecha_a_texto(item.get('fecha'))
        return jsonify({"estado": "exito", "data": item}), 200
    except pymysql.MySQLError as error:
        print(f"AVISO: no se pudo obtener el gasto: {error}")
        return jsonify({
            "estado": "error",
            "mensaje": "No se pudo consultar la base de datos.",
        }), 500

# CU-02d: Editar un gasto deducible
@contabilidad_bp.route('/gastos/<int:id_gasto>', methods=['PUT'])
@api_requerir_roles('Contador', 'Administrador')
def api_editar_gasto(id_gasto):
    """Actualiza un gasto deducible existente."""
    try:
        datos = request.get_json() or {}
        respuesta = editar_gasto_deducible(
            id_gasto=id_gasto,
            descripcion=datos.get('descripcion'),
            monto=datos.get('monto'),
            categoria=datos.get('categoria'),
            tercero=datos.get('tercero'),
            nit=datos.get('nit'),
            numero_documento=datos.get('numero_documento'),
            fecha=datos.get('fecha')
        )
        return jsonify({"estado": "exito", "data": respuesta}), 200
    except (ValueError, PermissionError) as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400

# CU-02e: Anular un gasto deducible
@contabilidad_bp.route('/gastos/<int:id_gasto>', methods=['DELETE'])
@api_requerir_roles('Contador', 'Administrador')
def api_anular_gasto(id_gasto):
    """Anula lógicamente un gasto deducible."""
    try:
        respuesta = anular_gasto_deducible(id_gasto)
        return jsonify({"estado": "exito", "data": respuesta}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400

# CU-03: Consolidar Información Contable
@contabilidad_bp.route('/consolidado', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_consolidar():
    """Devuelve la información contable consolidada del periodo."""
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    consolidado = consolidar_informacion_contable(f_inicio, f_fin)
    return jsonify({"estado": "exito", "data": consolidado}), 200

# CU-04: Balance General
@contabilidad_bp.route('/balance-general', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_balance_general():
    """Calcula y devuelve el Balance General del periodo."""
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        balance = calcular_balance_general(f_inicio, f_fin)
        return jsonify({"estado": "exito", "data": balance}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400

def _error_formato():
    """Respuesta JSON cuando el formato de exportación no es pdf ni excel."""
    return jsonify({
        "estado": "error",
        "mensaje": "Formato no soportado. Use 'pdf' o 'excel'.",
    }), 400


# CU-05: Exportar Reportes (PDF / Excel)
@contabilidad_bp.route('/exportar-reporte', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_exportar_reporte():
    """Exporta un reporte contable en PDF o Excel."""
    # tipo: estado_resultados | balance | consolidado
    tipo = request.args.get('tipo', 'estado_resultados').lower()
    formato = request.args.get('formato', 'pdf').lower()
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    try:
        if tipo == 'balance':
            datos, periodo_txt = obtener_balance_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_balance_general_pdf(datos, periodo_txt)
                nombre = 'balance_general.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_balance_general_excel(datos, periodo_txt)
                nombre = 'balance_general.xlsx'
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return _error_formato()
        elif tipo == 'consolidado':
            datos, periodo_txt = obtener_consolidado_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_consolidado_pdf(datos, periodo_txt)
                nombre = 'consolidado_contable.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_consolidado_excel(datos, periodo_txt)
                nombre = 'consolidado_contable.xlsx'
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return _error_formato()
        else:  # estado_resultados
            datos, periodo_txt = obtener_estado_resultados_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_estado_resultados_pdf(datos, periodo_txt)
                nombre = 'estado_resultados.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_estado_resultados_excel(datos, periodo_txt)
                nombre = 'estado_resultados.xlsx'
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return _error_formato()

        return send_file(stream, mimetype=mime, as_attachment=True, download_name=nombre)
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


# Rutas de renderizado HTML
AVISO_SIN_DATOS = (
    "Aún no hay movimientos registrados (ventas de inventario, nómina o "
    "gastos). Mostrando valores en cero."
)


@contabilidad_bp.route('/ver-estado-resultados', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_estado_resultados_html():
    """Muestra la página del Estado de Resultados."""
    aviso = None
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    try:
        datos = generar_estado_resultados(f_inicio, f_fin)
    except ValueError:
        aviso = AVISO_SIN_DATOS
        datos = {
            'ingresos_totales': 0.0, 'costo_ventas': 0.0,
            'utilidad_bruta': 0.0, 'gastos_operativos': 0.0,
            'desglose_gastos': {
                'nomina': 0.0, 'gastos_deducibles': 0.0,
                'perdidas_inventario': 0.0,
            },
            'utilidad_neta': 0.0,
        }
    return render_template('contabilidad/estado_resultados.html',
                           data=datos, aviso=aviso, fecha_inicio=f_inicio, fecha_fin=f_fin)


@contabilidad_bp.route('/ver-balance-general', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_balance_general_html():
    """Muestra la página del Balance General."""
    aviso = None
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    try:
        datos = calcular_balance_general(f_inicio, f_fin)
    except ValueError:
        aviso = AVISO_SIN_DATOS
        datos = {'activos': {'efectivo_caja': 0.0, 'inventario': 0.0, 'total_activos': 0.0},
                 'pasivos': {'pasivos_laborales': 0.0, 'total_pasivos': 0.0},
                 'patrimonio': {'utilidad_ejercicio': 0.0, 'total_patrimonio': 0.0}}
    return render_template('contabilidad/balance_general.html',
                           data=datos, aviso=aviso, fecha_inicio=f_inicio, fecha_fin=f_fin)


@contabilidad_bp.route('/ver-registrar-gasto', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_registrar_gasto_html():
    """Muestra el formulario para registrar un gasto."""
    return render_template('contabilidad/registrar_gasto.html')


@contabilidad_bp.route('/ver-listar-gastos', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_listar_gastos_html():
    """Muestra la página de gastos deducibles registrados."""
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    return render_template('contabilidad/listar_gastos.html',
                           fecha_inicio=f_inicio, fecha_fin=f_fin)


# ---------------------------------------------------------------------------
# Núcleo contable: PUC, comprobantes, libro mayor y balance de prueba
# ---------------------------------------------------------------------------

def _error_contable(error):
    """Respuesta JSON uniforme para errores del núcleo contable."""
    if isinstance(error, pymysql.MySQLError):
        print(f"AVISO: error de base de datos contable: {error}")
        return jsonify({
            "estado": "error",
            "mensaje": "No se pudo consultar la base de datos.",
        }), 500
    return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/puc', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_puc():
    """Busca cuentas del Plan Único de Cuentas."""
    try:
        termino = request.args.get('q') or request.args.get('termino')
        solo_movimiento = request.args.get('solo_movimiento', '1') != '0'
        cuentas = buscar_cuentas(termino, solo_movimiento=solo_movimiento)
        return jsonify({"estado": "exito", "data": cuentas}), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_contable(error)


@contabilidad_bp.route('/puc', methods=['POST'])
@api_requerir_roles('Administrador', 'Contador')
def api_crear_cuenta():
    """Agrega una cuenta personalizada al PUC."""
    try:
        datos = request.get_json() or {}
        id_cuenta = crear_cuenta(
            codigo=datos.get('codigo'),
            nombre=datos.get('nombre'),
            naturaleza=datos.get('naturaleza'),
            grupo=datos.get('grupo'),
            clase=datos.get('clase'),
        )
        return jsonify({
            "estado": "exito",
            "data": {"id_cuenta": id_cuenta},
            "mensaje": "Cuenta creada correctamente.",
        }), 201
    except (ValueError, pymysql.MySQLError) as error:
        return _error_contable(error)


@contabilidad_bp.route('/comprobantes', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_listar_comprobantes():
    """Lista comprobantes con filtros de fecha, estado y tipo."""
    try:
        comprobantes = listar_comprobantes(
            fecha_inicio=request.args.get('fecha_inicio'),
            fecha_fin=request.args.get('fecha_fin'),
            estado=request.args.get('estado'),
            tipo=request.args.get('tipo'),
        )
        return jsonify({"estado": "exito", "data": comprobantes}), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_contable(error)


@contabilidad_bp.route('/comprobantes', methods=['POST'])
@api_requerir_roles('Administrador', 'Contador')
def api_crear_comprobante():
    """Crea un comprobante contable balanceado."""
    try:
        datos = request.get_json() or {}
        resultado = crear_comprobante(
            tipo=datos.get('tipo'),
            fecha=datos.get('fecha'),
            descripcion=datos.get('descripcion'),
            lineas=datos.get('lineas') or [],
            id_usuario=session.get('usuario_id'),
            id_tercero=datos.get('id_tercero'),
            numero=datos.get('numero'),
        )
        return jsonify({
            "estado": "exito",
            "data": resultado,
            "mensaje": "Comprobante registrado correctamente.",
        }), 201
    except (ValueError, pymysql.MySQLError) as error:
        return _error_contable(error)


@contabilidad_bp.route('/comprobantes/<int:id_comprobante>', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_obtener_comprobante(id_comprobante):
    """Devuelve un comprobante con su detalle."""
    try:
        comprobante = obtener_comprobante(id_comprobante)
        if not comprobante:
            return jsonify({"estado": "error", "mensaje": "Comprobante no encontrado."}), 404
        return jsonify({"estado": "exito", "data": comprobante}), 200
    except pymysql.MySQLError as error:
        return _error_contable(error)


@contabilidad_bp.route('/comprobantes/<int:id_comprobante>/anular', methods=['POST'])
@api_requerir_roles('Administrador', 'Contador')
def api_anular_comprobante(id_comprobante):
    """Anula lógicamente un comprobante."""
    try:
        anular_comprobante(id_comprobante)
        return jsonify({"estado": "exito", "mensaje": "Comprobante anulado."}), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_contable(error)


@contabilidad_bp.route('/libro-mayor', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_libro_mayor():
    """Libro mayor de una cuenta con saldo corrido."""
    try:
        datos = libro_mayor(
            cuenta_codigo=request.args.get('cuenta') or request.args.get('codigo'),
            fecha_inicio=request.args.get('fecha_inicio'),
            fecha_fin=request.args.get('fecha_fin'),
            id_tercero=request.args.get('id_tercero'),
        )
        return jsonify({"estado": "exito", "data": datos}), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_contable(error)


@contabilidad_bp.route('/balance-prueba', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_balance_prueba():
    """Balance de prueba por cuenta."""
    try:
        datos = balance_prueba(
            fecha_inicio=request.args.get('fecha_inicio'),
            fecha_fin=request.args.get('fecha_fin'),
        )
        return jsonify({"estado": "exito", "data": datos}), 200
    except (ValueError, pymysql.MySQLError) as error:
        return _error_contable(error)


@contabilidad_bp.route('/ver-comprobantes', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_comprobantes_html():
    """Página de comprobantes contables."""
    return render_template('contabilidad/comprobantes.html')


@contabilidad_bp.route('/ver-libro-mayor', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_libro_mayor_html():
    """Página del libro mayor."""
    return render_template('contabilidad/libro_mayor.html')


@contabilidad_bp.route('/ver-balance-prueba', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_balance_prueba_html():
    """Página del balance de prueba."""
    f_inicio = request.args.get('fecha_inicio')
    f_fin = request.args.get('fecha_fin')
    try:
        datos = balance_prueba(f_inicio, f_fin)
    except (ValueError, pymysql.MySQLError) as error:
        print(f"AVISO: no se pudo calcular el balance de prueba: {error}")
        datos = {
            "cuentas": [], "total_debitos": 0.0, "total_creditos": 0.0,
            "diferencia": 0.0, "cuadra": True,
        }
    return render_template('contabilidad/balance_prueba.html', data=datos,
                           fecha_inicio=f_inicio, fecha_fin=f_fin)


@contabilidad_bp.route('/ver-puc', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_puc_html():
    """Página de consulta del Plan Único de Cuentas."""
    return render_template('contabilidad/puc.html')

