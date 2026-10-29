"""EXODUS Contable - aplicación principal.

Este es el único punto de entrada del sistema: contabilidad, inventario,
nómina y configuración comparten la misma base de datos, la misma sesión de
usuarios y la misma configuración (config.py).

Se puede ejecutar de dos formas:

    python run.py                  (desde la carpeta EXODUS, recomendado)
    python Modulo-contable/app.py  (desde cualquier carpeta)
"""

import os
import secrets
import sys

import pymysql
from flask import (Flask, abort, jsonify, redirect, render_template, request,
                   session, url_for)

RUTA_APP = os.path.dirname(os.path.abspath(__file__))
RUTA_PROYECTO = os.path.dirname(RUTA_APP)

# Los módulos viven en sus propias carpetas (../modulo-*). Se agregan al path
# para poder importarlos desde esta aplicación.
for carpeta in ('modulo-inventario', 'modulo-nomina', 'modulo-configuracion'):
    sys.path.insert(0, os.path.join(RUTA_PROYECTO, carpeta))

from config import DEBUG, HOST, PORT, clave_secreta  # noqa: E402
from configuracion import registrar_configuracion  # noqa: E402
from database.init_db import iniciar_db  # noqa: E402
from inventario import registrar_inventario  # noqa: E402
from nomina import registrar_nomina  # noqa: E402
from routes.auth import auth_bp  # noqa: E402
from routes.contabilidad import contabilidad_bp  # noqa: E402


def csrf_token():
    """Token CSRF de la sesión actual."""
    if 'csrf' not in session:
        session['csrf'] = secrets.token_hex(16)
    return session['csrf']


def crear_app():
    """Construye la aplicación completa (fábrica)."""
    app = Flask(
        __name__,
        template_folder=os.path.join(RUTA_APP, 'templates'),
        static_folder=os.path.join(RUTA_APP, 'static'),
    )
    app.config.update(
        SECRET_KEY=clave_secreta(),
        SESSION_COOKIE_HTTPONLY=True,
        SESSION_COOKIE_SAMESITE="Lax",
        MAX_CONTENT_LENGTH=16 * 1024 * 1024,
    )

    # Registro de Blueprints (módulos) de la aplicación
    app.register_blueprint(auth_bp)
    app.register_blueprint(contabilidad_bp, url_prefix='/api/contabilidad')
    registrar_inventario(app)      # /api/inventario (vista: /api/inventario/modulo)
    registrar_nomina(app)          # /api/nomina (vista: /api/nomina/modulo)
    registrar_configuracion(app)   # /configuracion (etiquetas, parámetros, roles, usuarios)

    app.jinja_env.globals['csrf_token'] = csrf_token

    @app.before_request
    def verificar_csrf():
        """Protege los formularios y exige JSON en las escrituras de la API.

        Los formularios HTML envían el token `csrf`. Las rutas /api/ que
        modifican datos deben enviar JSON (Content-Type: application/json),
        lo que impide que un formulario de otro sitio las use (CSRF).
        """
        if request.path.startswith('/api/'):
            if request.method in ('POST', 'PUT', 'PATCH') and request.content_length:
                if not request.is_json:
                    abort(415)
            return

        if request.method == 'POST':
            esperado = session.get('csrf', '')
            enviado = request.form.get('csrf', '')
            if not esperado or not enviado or not secrets.compare_digest(enviado, esperado):
                abort(400)

    @app.after_request
    def cabeceras(resp):
        """Agrega cabeceras de seguridad a todas las respuestas."""
        resp.headers['X-Content-Type-Options'] = 'nosniff'
        resp.headers['X-Frame-Options'] = 'DENY'
        resp.headers['Referrer-Policy'] = 'same-origin'
        resp.headers['Cache-Control'] = 'no-store'
        return resp

    @app.route('/')
    def inicio():
        """Página de inicio. Redirige al login si no hay sesión activa."""
        if not session.get('usuario_id'):
            return redirect(url_for('auth.login'))
        resumen = None
        try:
            from inventario.resumen import obtener_posicion_inventario
            from services.consolidacion_service import consolidar_informacion_contable

            resumen = {
                **obtener_posicion_inventario(),
                'ventas': consolidar_informacion_contable()['ingresos_totales'],
            }
        except (pymysql.MySQLError, KeyError, TypeError, ValueError) as error:
            # El inicio carga aunque la base de datos esté vacía o apagada.
            print(f"AVISO: no se pudo calcular el resumen del inicio: {error}")
        return render_template('dashboard.html', resumen=resumen)

    @app.errorhandler(400)
    def solicitud_invalida(_e):
        """Responde 400 cuando la petición no es válida."""
        return render_template(
            'error.html', titulo='Solicitud no válida',
            mensaje='La sesión expiró o el formulario no es válido. Vuelve a intentarlo.',
        ), 400

    @app.errorhandler(403)
    def sin_permiso(_e):
        """Responde 403 cuando el usuario no tiene permiso."""
        return render_template(
            'error.html', titulo='Sin acceso',
            mensaje='Tu rol no tiene permiso para entrar a esta sección.',
        ), 403

    @app.errorhandler(404)
    def no_encontrado(_e):
        """Responde 404 cuando la página no existe."""
        return render_template(
            'error.html', titulo='Página no encontrada',
            mensaje='La dirección no existe en Exodus Contable.',
        ), 404

    @app.errorhandler(415)
    def formato_no_soportado(_e):
        """Responde 415 cuando el tipo de contenido no se admite."""
        mensaje = 'Esta operación debe enviarse como JSON (Content-Type: application/json).'
        if request.path.startswith('/api/'):
            return jsonify({'error': mensaje}), 415
        return render_template('error.html', titulo='Formato no válido', mensaje=mensaje), 415

    try:
        iniciar_db()
    except (pymysql.MySQLError, OSError, ValueError) as error:
        # La aplicación arranca aunque la base de datos esté apagada.
        print(f"AVISO: no se pudo preparar la base de datos: {error}")

    return app


app = crear_app()


if __name__ == '__main__':
    app.run(host=HOST, port=PORT, debug=DEBUG)
