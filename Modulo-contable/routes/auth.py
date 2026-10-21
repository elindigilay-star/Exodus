import time
from functools import wraps

from flask import (Blueprint, abort, flash, redirect, render_template,
                   request, session, url_for)
from werkzeug.security import check_password_hash

from models.usuario import obtener_usuario_por_id, obtener_usuario_por_usuario

auth_bp = Blueprint('auth', __name__)

COOKIE_USUARIO = "exodus_usuario"
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 300

# El rol puede venir en la base en minúsculas (versiones viejas del script
# SQL) o con mayúscula inicial (versión actual). Aquí se unifica siempre a la
# forma con mayúscula inicial para que el resto del sistema compare sin líos.
ROLES_CANONICOS = {
    'administrador': 'Administrador',
    'contador': 'Contador',
    'auxiliar': 'Auxiliar',
    'empleado': 'Empleado',
}


def rol_canonico(valor):
    """Devuelve el rol en su forma estándar ('Administrador', 'Contador', ...)."""
    if not valor:
        return valor
    limpio = str(valor).strip()
    return ROLES_CANONICOS.get(limpio.lower(), limpio)

# (usuario, ip) -> [fallos, bloqueado_hasta]
_intentos = {}


def _bloqueado(clave):
    registro = _intentos.get(clave)
    if registro and registro[1] > time.time():
        return int(registro[1] - time.time()) // 60 + 1
    return 0


def _registrar_fallo(clave):
    fallos, _ = _intentos.get(clave, [0, 0])
    fallos += 1
    hasta = time.time() + BLOQUEO_SEGUNDOS if fallos >= MAX_INTENTOS else 0
    _intentos[clave] = [0 if hasta else fallos, hasta]


@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Inicia sesión con usuario y contraseña (mismo flujo que Exodus-login)."""
    if session.get('usuario_id'):
        return redirect(url_for('inicio'))

    recordado = request.cookies.get(COOKIE_USUARIO, "")
    valores = {"usuario_valor": recordado, "recordar": bool(recordado)}

    if request.method == 'POST':
        usuario_valor = (request.form.get('usuario') or '').strip()
        clave = request.form.get('clave') or ''
        recordar = request.form.get('recordar') == 'on'
        valores = {"usuario_valor": usuario_valor, "recordar": recordar}

        if not usuario_valor or not clave:
            flash("Escribe tu usuario y tu contraseña.", "error")
            return render_template('login.html', **valores), 400

        llave = (usuario_valor.lower(), request.remote_addr)
        minutos = _bloqueado(llave)
        if minutos:
            flash(f"Demasiados intentos fallidos. Espera {minutos} min e inténtalo de nuevo.", "error")
            return render_template('login.html', **valores), 429

        fila = obtener_usuario_por_usuario(usuario_valor)

        if fila is None or not fila.get('clave_hash') or not check_password_hash(fila['clave_hash'], clave):
            _registrar_fallo(llave)
            flash("Usuario o contraseña incorrectos.", "error")
            return render_template('login.html', **valores), 401

        if not fila['activo']:
            flash("Tu usuario está inactivo. Pide al administrador que lo active.", "error")
            return render_template('login.html', **valores), 403

        _intentos.pop(llave, None)
        session.clear()
        session['usuario_id'] = fila['id_usuario']
        session['usuario_nombre'] = fila['nombre']
        session['usuario_rol'] = rol_canonico(fila['rol'])

        respuesta = redirect(url_for('inicio'))
        if recordar:
            # Solo se guarda el nombre de usuario, nunca la contraseña.
            respuesta.set_cookie(COOKIE_USUARIO, fila['usuario'],
                                 max_age=60 * 60 * 24 * 30,
                                 httponly=True, samesite="Lax")
        else:
            respuesta.delete_cookie(COOKIE_USUARIO)
        return respuesta

    return render_template('login.html', **valores)


@auth_bp.route('/logout', methods=['GET', 'POST'])
def logout():
    """Cierra la sesión activa."""
    session.clear()
    return redirect(url_for('auth.login'))


def login_requerido(f):
    """Decorador para exigir una sesión activa (cualquier rol)."""
    @wraps(f)
    def funcion_decorada(*args, **kwargs):
        if not session.get('usuario_id'):
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return funcion_decorada


def requerir_roles(*roles_permitidos):
    """Decorador para restringir el acceso a rutas según el rol del usuario."""
    def decorador(f):
        @wraps(f)
        def funcion_decorada(*args, **kwargs):
            id_usuario = session.get('usuario_id')

            if not id_usuario:
                return redirect(url_for('auth.login'))

            usuario = obtener_usuario_por_id(id_usuario)

            if not usuario:
                abort(403)

            if rol_canonico(usuario['rol']) not in roles_permitidos:
                abort(403)

            return f(*args, **kwargs)
        return funcion_decorada
    return decorador
