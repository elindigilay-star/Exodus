"""Exodus Contable - Entry point principal (login + todos los módulos)."""
import os
import secrets
import sys

from flask import Flask, abort, redirect, render_template, request, session, url_for

# Añadir rutas de los módulos hermanos
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

RUTA_MODULO_INVENTARIO = os.path.join(BASE_DIR, 'modulo-inventario')
sys.path.insert(0, RUTA_MODULO_INVENTARIO)

RUTA_MODULO_NOMINA = os.path.join(BASE_DIR, 'modulo-nomina')
sys.path.insert(0, RUTA_MODULO_NOMINA)

RUTA_MODULO_CONFIGURACION = os.path.join(BASE_DIR, 'modulo-configuracion')
sys.path.insert(0, RUTA_MODULO_CONFIGURACION)

from inventario import registrar_inventario
from nomina import registrar_nomina
from configuracion import registrar_configuracion
from routes.auth import auth_bp
from routes.contabilidad import contabilidad_bp
from db import iniciar_db, cerrar_db

app = Flask(__name__)
app.config.update(
    SECRET_KEY=os.environ.get("EXODUS_SECRET_KEY", "exodus-contable-dev-secret-change-in-production"),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
app.teardown_appcontext(cerrar_db)

# Registro de Blueprints (módulos)
app.register_blueprint(auth_bp)
app.register_blueprint(contabilidad_bp, url_prefix='/api/contabilidad')
registrar_inventario(app)      # /api/inventario (vista: /api/inventario/modulo)
registrar_nomina(app)          # /api/nomina (vista: /api/nomina/modulo)
registrar_configuracion(app)   # /configuracion (etiquetas, parámetros, roles, usuarios)


def csrf_token():
    if 'csrf' not in session:
        session['csrf'] = secrets.token_hex(16)
    return session['csrf']


app.jinja_env.globals['csrf_token'] = csrf_token


@app.before_request
def verificar_csrf():
    """Protege los formularios contra CSRF. La API JSON queda exenta."""
    if request.method == 'POST' and not request.path.startswith('/api/'):
        enviado = request.form.get('csrf', '')
        if not secrets.compare_digest(enviado, session.get('csrf', '')):
            abort(400)


@app.after_request
def cabeceras(resp):
    resp.headers['X-Content-Type-Options'] = 'nosniff'
    resp.headers['X-Frame-Options'] = 'DENY'
    return resp


@app.route('/')
def inicio():
    """Dashboard principal. Redirige al login si no hay sesión."""
    if not session.get('usuario_id'):
        return redirect(url_for('auth.login'))
    resumen = None
    try:
        from inventario.resumen import obtener_posicion_inventario
        from services.consolidacion_service import consolidar_informacion_contable
        resumen = {**obtener_posicion_inventario(), 'ventas': consolidar_informacion_contable()['ingresos_totales']}
    except Exception as error:
        print(f"AVISO: no se pudo calcular el resumen del inicio: {error}")
    return render_template('dashboard.html', resumen=resumen)


@app.errorhandler(400)
def solicitud_invalida(_e):
    return render_template('error.html', titulo='Solicitud no válida',
                           mensaje='La sesión expiró o el formulario no es válido. Vuelve a intentarlo.'), 400


@app.errorhandler(403)
def sin_permiso(_e):
    return render_template('error.html', titulo='Sin acceso',
                           mensaje='Tu rol no tiene permiso para entrar a esta sección.'), 403


@app.errorhandler(404)
def no_encontrado(_e):
    return render_template('error.html', titulo='Página no encontrada',
                           mensaje='La dirección no existe en Exodus Contable.'), 404


# Copiar templates necesarios de Modulo-contable que no existen aquí
# dashboard.html, error.html, base.html (ya tiene el login, pero necesita base para dashboard)

try:
    iniciar_db()
except Exception as error:
    print(f"AVISO: no se pudo preparar la base de datos: {error}")


if __name__ == '__main__':
    app.run(debug=True, port=5000)