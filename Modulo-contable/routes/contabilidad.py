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
    exportar_libro_diario_pdf, exportar_libro_diario_excel,
    exportar_libro_mayor_pdf, exportar_libro_mayor_excel,
    exportar_balance_comprobacion_pdf, exportar_balance_comprobacion_excel,
    obtener_estado_resultados_con_periodo, obtener_balance_con_periodo,
    obtener_consolidado_con_periodo,
    obtener_libro_diario_con_periodo, obtener_libro_mayor_con_periodo,
    obtener_balance_comprobacion_con_periodo
)
from services.asiento_service import (
    registrar_asiento, editar_asiento, contabilizar, anular,
    listar as listar_asientos_svc, obtener as obtener_asiento_svc
)
from services.libro_diario_service import generar_libro_diario, generar_libro_diario_resumido
from models.plan_cuentas import (
    listar_cuentas as listar_cuentas_svc,
    crear_cuenta as crear_cuenta_svc,
    actualizar_cuenta as actualizar_cuenta_svc,
    eliminar_cuenta as eliminar_cuenta_svc,
    obtener_arbol_cuentas as obtener_arbol_cuentas_svc,
)
from services.libro_mayor_service import (
    generar_libro_mayor, obtener_movimientos_cuenta
)
from services.balance_comprobacion_service import generar_balance_comprobacion
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
        elif tipo == 'libro_diario':
            datos, periodo_txt = obtener_libro_diario_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_libro_diario_pdf(datos, periodo_txt)
                nombre = 'libro_diario.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_libro_diario_excel(datos, periodo_txt)
                nombre = 'libro_diario.xlsx'
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return _error_formato()
        elif tipo == 'libro_mayor':
            datos, periodo_txt = obtener_libro_mayor_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_libro_mayor_pdf(datos, periodo_txt)
                nombre = 'libro_mayor.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_libro_mayor_excel(datos, periodo_txt)
                nombre = 'libro_mayor.xlsx'
                mime = 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
            else:
                return _error_formato()
        elif tipo == 'balance_comprobacion':
            datos, periodo_txt = obtener_balance_comprobacion_con_periodo(f_inicio, f_fin)
            if formato == 'pdf':
                stream = exportar_balance_comprobacion_pdf(datos, periodo_txt)
                nombre = 'balance_comprobacion.pdf'
                mime = 'application/pdf'
            elif formato == 'excel':
                stream = exportar_balance_comprobacion_excel(datos, periodo_txt)
                nombre = 'balance_comprobacion.xlsx'
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


# ============================================================================
# PLAN DE CUENTAS (API)
# ============================================================================

@contabilidad_bp.route('/plan-cuentas', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_listar_plan_cuentas():
    """Lista el plan de cuentas contables."""
    try:
        activo = request.args.get('activo')
        solo_movimiento = request.args.get('solo_movimiento') == '1'
        cuentas = listar_cuentas_svc(activo=activo, solo_movimiento=solo_movimiento)
        return jsonify({"estado": "exito", "data": cuentas}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/plan-cuentas', methods=['POST'])
@api_requerir_roles('Administrador', 'Contador')
def api_crear_plan_cuenta():
    """Crea una nueva cuenta contable."""
    try:
        datos = request.get_json() or {}
        id_cuenta = crear_cuenta_svc(
            codigo=datos.get('codigo'),
            nombre=datos.get('nombre'),
            tipo=datos.get('tipo', 'cuenta'),
            naturaleza=datos.get('naturaleza', 'ninguna'),
            cuenta_padre_id=datos.get('cuenta_padre_id'),
            nivel=int(datos.get('nivel', 1)),
            permite_movimiento=datos.get('permite_movimiento', 1),
            activo=datos.get('activo', 1),
        )
        return jsonify({"estado": "exito", "mensaje": "Cuenta contable creada.",
                        "id_cuenta": id_cuenta}), 201
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/plan-cuentas/<int:id_cuenta>', methods=['PUT'])
@api_requerir_roles('Administrador', 'Contador')
def api_editar_plan_cuenta(id_cuenta):
    """Edita una cuenta contable existente."""
    try:
        datos = request.get_json() or {}
        filas = actualizar_cuenta_svc(
            id_cuenta=id_cuenta,
            codigo=datos.get('codigo'),
            nombre=datos.get('nombre'),
            tipo=datos.get('tipo', 'cuenta'),
            naturaleza=datos.get('naturaleza', 'ninguna'),
            cuenta_padre_id=datos.get('cuenta_padre_id'),
            nivel=int(datos.get('nivel', 1)),
            permite_movimiento=datos.get('permite_movimiento', 1),
            activo=datos.get('activo', 1),
        )
        return jsonify({"estado": "exito", "mensaje": "Cuenta contable actualizada."}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/plan-cuentas/<int:id_cuenta>', methods=['DELETE'])
@api_requerir_roles('Administrador', 'Contador')
def api_eliminar_plan_cuenta(id_cuenta):
    """Elimina lógicamente una cuenta contable."""
    try:
        filas = eliminar_cuenta_svc(id_cuenta)
        return jsonify({"estado": "exito", "mensaje": "Cuenta contable eliminada."}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/plan-cuentas/arbol', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_arbol_plan_cuentas():
    """Retorna el plan de cuentas organizado como árbol jerárquico."""
    try:
        arbol = obtener_arbol_cuentas_svc()
        return jsonify({"estado": "exito", "data": arbol}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


# ============================================================================
# ASIENTOS CONTABLES (API)
# ============================================================================

@contabilidad_bp.route('/asientos', methods=['POST'])
@api_requerir_roles('Contador', 'Administrador')
def api_crear_asiento():
    """Crea un asiento contable con doble entrada."""
    try:
        datos = request.get_json() or {}
        id_usuario = session.get('usuario_id')
        id_asiento = registrar_asiento(
            numero_asiento=datos.get('numero_asiento'),
            fecha=datos.get('fecha'),
            descripcion=datos.get('descripcion'),
            id_usuario=id_usuario,
            referencia=datos.get('referencia'),
            movimientos=datos.get('movimientos', []),
        )
        return jsonify({
            "estado": "exito",
            "mensaje": "Asiento contable creado en estado BORRADOR.",
            "id_asiento": id_asiento,
        }), 201
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/asientos', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_listar_asientos():
    """Lista asientos contables con totales de debe y haber."""
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        estado = request.args.get('estado')
        asientos = listar_asientos_svc(
            fecha_inicio=f_inicio, fecha_fin=f_fin, estado=estado
        )
        # Convertir fechas a string para JSON serializable
        resultado = []
        for a in asientos:
            item = dict(a)
            item['fecha'] = fecha_a_texto(item.get('fecha'))
            item['fecha_creacion'] = fecha_a_texto(item.get('fecha_creacion'))
            item['fecha_contabilizacion'] = fecha_a_texto(item.get('fecha_contabilizacion'))
            resultado.append(item)
        return jsonify({"estado": "exito", "data": resultado}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/asientos/<int:id_asiento>', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_obtener_asiento(id_asiento):
    """Obtiene un asiento contable con todos sus movimientos."""
    try:
        asiento = obtener_asiento_svc(id_asiento)
        if not asiento:
            return jsonify({"estado": "error", "mensaje": "Asiento no encontrado."}), 404
        item = dict(asiento)
        item['fecha'] = fecha_a_texto(item.get('fecha'))
        item['fecha_creacion'] = fecha_a_texto(item.get('fecha_creacion'))
        item['fecha_contabilizacion'] = fecha_a_texto(item.get('fecha_contabilizacion'))
        # Convertir movimientos
        movs = []
        for m in item.get('movimientos', []):
            mv = dict(m)
            mv['debe'] = float(mv.get('debe', 0) or 0)
            mv['haber'] = float(mv.get('haber', 0) or 0)
            mv['base_gravable'] = float(mv.get('base_gravable', 0) or 0)
            mv['valor_iva'] = float(mv.get('valor_iva', 0) or 0)
            movs.append(mv)
        item['movimientos'] = movs
        return jsonify({"estado": "exito", "data": item}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/asientos/<int:id_asiento>', methods=['PUT'])
@api_requerir_roles('Contador', 'Administrador')
def api_editar_asiento(id_asiento):
    """Edita un asiento contable en borrador."""
    try:
        datos = request.get_json() or {}
        filas = editar_asiento(
            id_asiento=id_asiento,
            fecha=datos.get('fecha'),
            descripcion=datos.get('descripcion'),
            referencia=datos.get('referencia'),
            movimientos=datos.get('movimientos', []),
        )
        return jsonify({"estado": "exito", "mensaje": "Asiento actualizado."}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/asientos/<int:id_asiento>/contabilizar', methods=['POST'])
@api_requerir_roles('Contador', 'Administrador')
def api_contabilizar_asiento(id_asiento):
    """Contabiliza un asiento (BORRADOR -> CONTABLE)."""
    try:
        filas = contabilizar(id_asiento)
        return jsonify({"estado": "exito", "mensaje": "Asiento contabilizado."}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/asientos/<int:id_asiento>/anular', methods=['POST'])
@api_requerir_roles('Contador', 'Administrador')
def api_anular_asiento(id_asiento):
    """Anula un asiento contable."""
    try:
        filas = anular(id_asiento)
        return jsonify({"estado": "exito", "mensaje": "Asiento anulado."}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


# ============================================================================
# LIBRO DIARIO (API)
# ============================================================================

@contabilidad_bp.route('/libro-diario', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_libro_diario():
    """Devuelve el libro diaro con asientos y movimientos."""
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        estado = request.args.get('estado', 'CONTABLE')
        diario = generar_libro_diario(
            fecha_inicio=f_inicio, fecha_fin=f_fin, estado=estado
        )
        return jsonify({"estado": "exito", "data": diario}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


# ============================================================================
# LIBRO MAYOR (API)
# ============================================================================

@contabilidad_bp.route('/libro-mayor', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_libro_mayor():
    """Devuelve el libro mayor con saldos por cuenta."""
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        id_cuenta = request.args.get('id_cuenta')
        id_cuenta = int(id_cuenta) if id_cuenta else None
        mayor = generar_libro_mayor(
            fecha_inicio=f_inicio, fecha_fin=f_fin, id_cuenta=id_cuenta
        )
        return jsonify({"estado": "exito", "data": mayor}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


@contabilidad_bp.route('/libro-mayor/<int:id_cuenta>/movimientos', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_movimientos_cuenta(id_cuenta):
    """Devuelve los movimientos detallados de una cuenta contable."""
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        movimientos = obtener_movimientos_cuenta(
            id_cuenta=id_cuenta,
            fecha_inicio=f_inicio,
            fecha_fin=f_fin,
        )
        return jsonify({"estado": "exito", "data": movimientos}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


# ============================================================================
# BALANCE DE COMPROBACIÓN (API)
# ============================================================================

@contabilidad_bp.route('/balance-comprobacion', methods=['GET'])
@api_requerir_roles('Administrador', 'Contador')
def api_balance_comprobacion():
    """Devuelve el balance de comprobación (prueba de saldos)."""
    try:
        f_inicio = request.args.get('fecha_inicio')
        f_fin = request.args.get('fecha_fin')
        balance = generar_balance_comprobacion(
            fecha_inicio=f_inicio, fecha_fin=f_fin
        )
        return jsonify({"estado": "exito", "data": balance}), 200
    except ValueError as error:
        return jsonify({"estado": "error", "mensaje": str(error)}), 400


# ============================================================================
# Vistas HTML (renderizado)
# ============================================================================

@contabilidad_bp.route('/ver-plan-cuentas', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_plan_cuentas_html():
    """Muestra la página del Plan de Cuentas."""
    return render_template('contabilidad/plan_cuentas.html')


@contabilidad_bp.route('/ver-asientos', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_asientos_html():
    """Muestra la página de Asientos Contables."""
    return render_template('contabilidad/asientos.html')


@contabilidad_bp.route('/ver-libro-diario', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_libro_diario_html():
    """Muestra la página del Libro Diario."""
    return render_template('contabilidad/libro_diario.html')


@contabilidad_bp.route('/ver-libro-mayor', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_libro_mayor_html():
    """Muestra la página del Libro Mayor."""
    return render_template('contabilidad/libro_mayor.html')


@contabilidad_bp.route('/ver-balance-comprobacion', methods=['GET'])
@requerir_roles('Administrador', 'Contador')
def ver_balance_comprobacion_html():
    """Muestra la página del Balance de Comprobación."""
    return render_template('contabilidad/balance_comprobacion.html')
