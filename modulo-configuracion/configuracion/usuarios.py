import re

import pymysql
from flask import (abort, flash, redirect, render_template,
                   request, session, url_for)

from models import usuario as modelo
from routes.auth import requerir_roles

from .rutas import configuracion_bp

ROLES_VALIDOS = ('Administrador', 'Contador', 'Auxiliar', 'Empleado')
PATRON_USUARIO = re.compile(r'^[A-Za-z0-9._-]{3,50}$')
DOMINIO_EMAIL = 'exodo.local'


def _render(v=None, editar=None):
    return render_template(
        'configuracion/usuarios.html',
        lista=modelo.listar_usuarios(),
        roles=ROLES_VALIDOS,
        v=v or {},
        editar=editar,
    )


def _a_booleano(valor):
    return valor == 'on'


@configuracion_bp.route('/configuracion/usuarios', methods=['GET', 'POST'])
@requerir_roles('Administrador')
def usuarios():
    if request.method == 'POST':
        usuario = (request.form.get('usuario') or '').strip()
        nombre = (request.form.get('nombre') or '').strip()
        rol = request.form.get('rol') or ''
        clave = request.form.get('clave') or ''
        email = (request.form.get('email') or '').strip()
        activo = _a_booleano(request.form.get('activo'))

        v = {'usuario': usuario, 'nombre': nombre, 'rol': rol,
             'email': email, 'activo': activo}

        error = None
        if not PATRON_USUARIO.match(usuario):
            error = 'El usuario debe tener de 3 a 50 caracteres: letras, números, punto, guion o guion bajo.'
        elif not nombre:
            error = 'Escribe el nombre completo.'
        elif rol not in ROLES_VALIDOS:
            error = 'Elige un rol válido.'
        elif len(clave) < 8:
            error = 'La contraseña debe tener al menos 8 caracteres.'
        elif modelo.existe_usuario(usuario):
            error = 'Ya existe un usuario con ese nombre de usuario.'
        elif email and modelo.existe_email(email):
            error = 'Ya existe un usuario con ese email.'

        if error:
            flash(error, 'error')
            return _render(v)

        if not email:
            email = f'{usuario}@{DOMINIO_EMAIL}'
            if modelo.existe_email(email):
                flash('Ya existe un usuario con ese email generado. Escribe uno distinto.', 'error')
                return _render(v)

        try:
            modelo.crear_usuario(nombre, usuario, email, rol, clave, activo)
        except pymysql.err.IntegrityError:
            flash('No se pudo crear: el usuario o el email ya están en uso.', 'error')
            return _render(v)

        flash('Usuario creado.', 'ok')
        return redirect(url_for('configuracion.usuarios'))

    return _render()


@configuracion_bp.route('/configuracion/usuarios/<int:id>/editar', methods=['GET', 'POST'])
@requerir_roles('Administrador')
def editar(id):
    fila = modelo.obtener_usuario_completo(id)
    if fila is None:
        abort(404)

    v = {'usuario': fila['usuario'], 'nombre': fila['nombre'],
         'rol': fila['rol'], 'email': fila['email'], 'activo': bool(fila['activo'])}

    if request.method == 'POST':
        nombre = (request.form.get('nombre') or '').strip()
        rol = request.form.get('rol') or ''
        clave = request.form.get('clave') or ''
        email = (request.form.get('email') or '').strip() or fila['email']
        activo = _a_booleano(request.form.get('activo'))

        v = {'usuario': fila['usuario'], 'nombre': nombre, 'rol': rol,
             'email': email, 'activo': activo}

        error = None
        if not nombre:
            error = 'Escribe el nombre completo.'
        elif rol not in ROLES_VALIDOS:
            error = 'Elige un rol válido.'
        elif clave and len(clave) < 8:
            error = 'La nueva contraseña debe tener al menos 8 caracteres.'
        elif modelo.existe_email(email, excluir_id=id):
            error = 'Ya existe otro usuario con ese email.'

        if not error:
            deja_de_ser_admin = (rol or '').strip().lower() != 'administrador' or not activo
            if id == session.get('usuario_id') and ((rol or '').strip().lower() != (fila['rol'] or '').strip().lower() or not activo):
                error = 'No puedes cambiar tu propio rol ni desactivarte.'
            elif ((fila['rol'] or '').strip().lower() == 'administrador' and fila['activo']
                  and deja_de_ser_admin and modelo.contar_admins_activos(excluir_id=id) == 0):
                error = 'Debe quedar al menos un administrador activo.'

        if error:
            flash(error, 'error')
            return _render(v, editar=fila)

        try:
            modelo.actualizar_usuario(id, nombre, rol, activo, clave or None)
        except pymysql.err.IntegrityError:
            flash('No se pudo actualizar: el email ya está en uso.', 'error')
            return _render(v, editar=fila)

        flash('Usuario actualizado.', 'ok')
        return redirect(url_for('configuracion.usuarios'))

    return _render(v, editar=fila)


@configuracion_bp.route('/configuracion/usuarios/<int:id>/eliminar', methods=['POST'])
@requerir_roles('Administrador')
def eliminar(id):
    fila = modelo.obtener_usuario_completo(id)
    if fila is None:
        abort(404)

    if id == session.get('usuario_id'):
        flash('No puedes eliminar tu propio usuario.', 'error')
    elif ((fila['rol'] or '').strip().lower() == 'administrador' and fila['activo']
          and modelo.contar_admins_activos(excluir_id=id) == 0):
        flash('Debe quedar al menos un administrador activo.', 'error')
    else:
        modelo.eliminar_usuario(id)
        flash('Usuario desactivado. Ya no puede iniciar sesión.', 'ok')

    return redirect(url_for('configuracion.usuarios'))
