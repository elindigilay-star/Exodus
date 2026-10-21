import pymysql
from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from db import get_db
from seguridad import rol_requerido

bp = Blueprint("roles", __name__, url_prefix="/configuracion/roles")
ROLES = ("administrador",)


def _listar():
    return get_db().execute("SELECT * FROM roles ORDER BY nombre").fetchall()


def _listar_con_permisos():
    roles = _listar()
    db = get_db()
    for rol in roles:
        perms = db.execute(
            """SELECT p.id, p.nombre, p.descripcion
               FROM permisos p
               JOIN rol_permiso rp ON rp.permiso_id = p.id
               WHERE rp.rol_id = %s
               ORDER BY p.nombre""",
            (rol["id"],),
        ).fetchall()
        rol["permisos"] = perms
        rol["permisos_ids"] = [p["id"] for p in perms]
    return roles


def _todos_permisos():
    return get_db().execute("SELECT * FROM permisos ORDER BY nombre").fetchall()


def _leer_formulario():
    nombre = request.form.get("nombre", "").strip()
    descripcion = request.form.get("descripcion", "").strip()
    permisos = request.form.getlist("permisos")
    if not nombre:
        return None, "Escribe el nombre del rol."
    return (nombre, descripcion, [int(p) for p in permisos]), None


def _asignar_permisos(rol_id, permisos_ids):
    db = get_db()
    db.execute("DELETE FROM rol_permiso WHERE rol_id = %s", (rol_id,))
    if permisos_ids:
        db.executemany(
            "INSERT INTO rol_permiso (rol_id, permiso_id) VALUES (%s,%s)",
            [(rol_id, p) for p in permisos_ids],
        )


@bp.route("/", methods=["GET", "POST"])
@rol_requerido(*ROLES)
def index():
    if request.method == "POST":
        datos, error = _leer_formulario()
        if error:
            flash(error, "error")
        else:
            try:
                db = get_db()
                cur = db.execute(
                    "INSERT INTO roles (nombre, descripcion) VALUES (%s,%s)",
                    (datos[0], datos[1]),
                )
                db.commit()
                _asignar_permisos(cur.lastrowid, datos[2])
                db.commit()
                flash("Rol creado.", "ok")
                return redirect(url_for("roles.index"))
            except pymysql.err.IntegrityError:
                flash("Ya existe un rol con ese nombre.", "error")
    return render_template(
        "configuracion/roles.html",
        lista=_listar_con_permisos(),
        todos_permisos=_todos_permisos(),
        editar=None,
    )


@bp.route("/<int:id>/editar", methods=["GET", "POST"])
@rol_requerido(*ROLES)
def editar(id):
    db = get_db()
    fila = db.execute("SELECT * FROM roles WHERE id = %s", (id,)).fetchone()
    if fila is None:
        abort(404)
    perms_actuales = db.execute(
        "SELECT permiso_id FROM rol_permiso WHERE rol_id = %s", (id,)
    ).fetchall()
    editar_data = {**fila, "permisos_ids": [p["permiso_id"] for p in perms_actuales]}
    if request.method == "POST":
        datos, error = _leer_formulario()
        if error:
            flash(error, "error")
        else:
            try:
                db.execute(
                    "UPDATE roles SET nombre=%s, descripcion=%s WHERE id=%s",
                    (datos[0], datos[1], id),
                )
                _asignar_permisos(id, datos[2])
                db.commit()
                flash("Rol actualizado.", "ok")
                return redirect(url_for("roles.index"))
            except pymysql.err.IntegrityError:
                flash("Ya existe un rol con ese nombre.", "error")
    return render_template(
        "configuracion/roles.html",
        lista=_listar_con_permisos(),
        todos_permisos=_todos_permisos(),
        editar=editar_data,
    )


@bp.route("/<int:id>/eliminar", methods=["POST"])
@rol_requerido(*ROLES)
def eliminar(id):
    db = get_db()
    fila = db.execute("SELECT * FROM roles WHERE id = %s", (id,)).fetchone()
    if fila is None:
        abort(404)
    en_uso = db.execute(
        "SELECT COUNT(*) AS n FROM usuarios WHERE rol = %s AND activo = 1",
        (fila["nombre"],),
    ).fetchone()["n"]
    if en_uso > 0:
        flash(f"No se puede eliminar: hay {en_uso} usuario(s) activo(s) con este rol.", "error")
    else:
        db.execute("DELETE FROM roles WHERE id = %s", (id,))
        db.commit()
        flash("Rol eliminado.", "ok")
    return redirect(url_for("roles.index"))
