import re

import pymysql
from flask import Blueprint, abort, flash, g, redirect, render_template, request, url_for
from werkzeug.security import generate_password_hash

from db import get_db
from seguridad import rol_requerido

bp = Blueprint("usuarios", __name__)
ROLES_VALIDOS = ("administrador", "contador", "rrhh")
PATRON_USUARIO = re.compile(r"^[A-Za-z0-9._-]{3,50}$")
V_NUEVO = {"usuario": "", "nombre": "", "rol": "contador", "activo": True}


def _listar():
    return get_db().execute(
        "SELECT id, usuario, nombre, rol, activo FROM usuarios ORDER BY usuario"
    ).fetchall()


def _otros_admins_activos(excluir_id):
    fila = get_db().execute(
        "SELECT COUNT(*) AS n FROM usuarios WHERE rol = 'administrador' AND activo = 1 AND id <> %s",
        (excluir_id,),
    ).fetchone()
    return fila["n"]


def _valores_form():
    return {
        "usuario": request.form.get("usuario", "").strip(),
        "nombre": request.form.get("nombre", "").strip(),
        "rol": request.form.get("rol", ""),
        "activo": request.form.get("activo") == "on",
    }


def _validar(v, clave, creando):
    if creando and not PATRON_USUARIO.match(v["usuario"]):
        return "El usuario debe tener de 3 a 50 caracteres: letras, números, punto, guion o guion bajo."
    if not v["nombre"]:
        return "Escribe el nombre completo."
    if v["rol"] not in ROLES_VALIDOS:
        return "Elige un rol válido."
    if creando and len(clave) < 8:
        return "La contraseña debe tener al menos 8 caracteres."
    if not creando and clave and len(clave) < 8:
        return "La nueva contraseña debe tener al menos 8 caracteres."
    return None


def _render(v, editar=None):
    return render_template("configuracion/usuarios.html", lista=_listar(), v=v, editar=editar)


@bp.route("/configuracion/usuarios", methods=["GET", "POST"])
@rol_requerido("administrador")
def usuarios():
    if request.method == "POST":
        v = _valores_form()
        clave = request.form.get("clave", "")
        error = _validar(v, clave, creando=True)
        if error:
            flash(error, "error")
            return _render(v)
        try:
            db = get_db()
            db.execute(
                "INSERT INTO usuarios (usuario, nombre, clave_hash, rol, activo) VALUES (%s,%s,%s,%s,%s)",
                (v["usuario"], v["nombre"], generate_password_hash(clave), v["rol"], int(v["activo"])),
            )
            db.commit()
            flash("Usuario creado.", "ok")
            return redirect(url_for("usuarios.usuarios"))
        except pymysql.err.IntegrityError:
            flash("Ya existe un usuario con ese nombre de usuario.", "error")
            return _render(v)
    return _render(dict(V_NUEVO))


@bp.route("/configuracion/usuarios/<int:id>/editar", methods=["GET", "POST"])
@rol_requerido("administrador")
def editar(id):
    db = get_db()
    fila = db.execute("SELECT * FROM usuarios WHERE id = %s", (id,)).fetchone()
    if fila is None:
        abort(404)
    v = {"usuario": fila["usuario"], "nombre": fila["nombre"],
         "rol": fila["rol"], "activo": bool(fila["activo"])}

    if request.method == "POST":
        nuevo = _valores_form()
        nuevo["usuario"] = fila["usuario"]
        clave = request.form.get("clave", "")
        error = _validar(nuevo, clave, creando=False)
        if not error:
            deja_de_ser_admin = nuevo["rol"] != "administrador" or not nuevo["activo"]
            if id == g.usuario["id"] and (nuevo["rol"] != fila["rol"] or not nuevo["activo"]):
                error = "No puedes cambiar tu propio rol ni desactivarte."
            elif (fila["rol"] == "administrador" and fila["activo"] and deja_de_ser_admin
                  and _otros_admins_activos(id) == 0):
                error = "Debe quedar al menos un administrador activo."
        if error:
            flash(error, "error")
            return _render(nuevo, editar=fila)
        if clave:
            db.execute(
                "UPDATE usuarios SET nombre=%s, rol=%s, activo=%s, clave_hash=%s WHERE id=%s",
                (nuevo["nombre"], nuevo["rol"], int(nuevo["activo"]), generate_password_hash(clave), id),
            )
        else:
            db.execute(
                "UPDATE usuarios SET nombre=%s, rol=%s, activo=%s WHERE id=%s",
                (nuevo["nombre"], nuevo["rol"], int(nuevo["activo"]), id),
            )
        db.commit()
        flash("Usuario actualizado.", "ok")
        return redirect(url_for("usuarios.usuarios"))

    return _render(v, editar=fila)


@bp.route("/configuracion/usuarios/<int:id>/eliminar", methods=["POST"])
@rol_requerido("administrador")
def eliminar(id):
    db = get_db()
    fila = db.execute("SELECT * FROM usuarios WHERE id = %s", (id,)).fetchone()
    if fila is None:
        abort(404)
    if id == g.usuario["id"]:
        flash("No puedes eliminar tu propio usuario.", "error")
    elif fila["rol"] == "administrador" and fila["activo"] and _otros_admins_activos(id) == 0:
        flash("Debe quedar al menos un administrador activo.", "error")
    else:
        db.execute("DELETE FROM usuarios WHERE id = %s", (id,))
        db.commit()
        flash("Usuario eliminado.", "ok")
    return redirect(url_for("usuarios.usuarios"))