"""Exodus Contable - página de inicio (login + menú principal por rol)."""
import os
import secrets
import time
from datetime import datetime

from flask import (Flask, abort, flash, g, redirect, render_template,
                   request, session, url_for)
from itsdangerous import URLSafeTimedSerializer, BadSignature, SignatureExpired
from werkzeug.security import check_password_hash

from db import INSTANCE_DIR, get_db, cerrar_db, iniciar_db
from seguridad import login_requerido
from modulos.configuracion import bp as configuracion_bp
from modulos.usuarios import bp as usuarios_bp
from modulos.parametros import bp as parametros_bp
from modulos.roles import bp as roles_bp
COOKIE_USUARIO = "exodus_usuario"
MAX_INTENTOS = 5
BLOQUEO_SEGUNDOS = 300
_serializer = None


def _get_serializer():
    global _serializer
    if _serializer is None:
        _serializer = URLSafeTimedSerializer(
            app.config["SECRET_KEY"], salt="exodus-recordar"
        )
    return _serializer


def _clave_secreta():
    ruta = os.path.join(INSTANCE_DIR, "secret_key")
    if os.path.exists(ruta):
        with open(ruta) as f:
            return f.read().strip()
    clave = secrets.token_hex(32)
    with open(ruta, "w") as f:
        f.write(clave)
    return clave


app = Flask(__name__)
app.config.update(
    SECRET_KEY=_clave_secreta(),
    SESSION_COOKIE_HTTPONLY=True,
    SESSION_COOKIE_SAMESITE="Lax",
)
app.teardown_appcontext(cerrar_db)
app.register_blueprint(configuracion_bp)
app.register_blueprint(usuarios_bp)
app.register_blueprint(parametros_bp)
app.register_blueprint(roles_bp)

ROLES = {
    "administrador": "Administrador",
    "contador": "Contador",
    "rrhh": "Recursos Humanos",
}

MODULOS = [
    {
        "slug": "inventario", "nombre": "Inventario", "color": "#0E7C7B",
        "descripcion": "Registra productos, controla entradas y salidas de stock.",
        "roles": ["administrador", "contador"],
        "requisitos": [
            ("RF-01", "Registrar productos"),
            ("RF-02", "Registrar entradas de inventario"),
            ("RF-03", "Registrar salidas de inventario"),
            ("RF-04", "Clasificar productos"),
            ("RF-05", "Administración integral de productos"),
        ],
    },
    {
        "slug": "nomina", "nombre": "Nómina", "color": "#C98A12",
        "descripcion": "Gestiona empleados, calcula salarios y registra novedades.",
        "roles": ["administrador", "rrhh"],
        "requisitos": [
            ("RF-06", "Registrar empleados"),
            ("RF-07", "Eliminar empleados"),
            ("RF-08", "Calcular nómina"),
            ("RF-09", "Registrar novedades laborales"),
        ],
    },
    {
        "slug": "contabilidad", "nombre": "Contabilidad", "color": "#3A5BA0",
        "descripcion": "Consolida la información y genera los estados financieros.",
        "roles": ["administrador", "contador"],
        "requisitos": [
            ("RF-10", "Generar estado de resultados"),
            ("RF-11", "Registrar gastos deducibles"),
            ("RF-12", "Consolidar información contable"),
            ("RF-13", "Calcular balance general"),
            ("RF-14", "Generar reportes contables"),
        ],
    },
    {
        "slug": "configuracion", "nombre": "Configuración", "color": "#7A4E8C",
        "descripcion": "Etiquetas, parámetros legales, usuarios, roles y permisos.",
        "roles": ["administrador", "contador"],
        "requisitos": [
            ("RF-15", "Gestionar etiquetas"),
            ("RF-16", "Ajustar parámetros"),
            ("RF-17", "Gestionar usuarios"),
            ("RF-18", "Gestionar roles y permisos"),
        ],
    },
]
MODULOS_POR_SLUG = {m["slug"]: m for m in MODULOS}

MESES = ["enero", "febrero", "marzo", "abril", "mayo", "junio", "julio",
         "agosto", "septiembre", "octubre", "noviembre", "diciembre"]
DIAS = ["lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo"]


def csrf_token():
    if "csrf" not in session:
        session["csrf"] = secrets.token_hex(16)
    return session["csrf"]


app.jinja_env.globals["csrf_token"] = csrf_token

_intentos = {}  # (usuario, ip) -> [fallos, bloqueado_hasta]


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


@app.before_request
def verificar_csrf():
    if request.method == "POST":
        enviado = request.form.get("csrf", "")
        if not secrets.compare_digest(enviado, session.get("csrf", "")):
            abort(400)


@app.before_request
def cargar_usuario():
    g.usuario = None
    uid = session.get("uid")
    if uid:
        fila = get_db().execute(
            "SELECT * FROM usuarios WHERE id = %s AND activo = 1", (uid,)
        ).fetchone()
        if fila:
            g.usuario = fila
        else:
            session.pop("uid", None)


@app.context_processor
def contexto():
    return {"usuario": g.get("usuario"), "roles": ROLES}


@app.after_request
def cabeceras(resp):
    resp.headers["X-Content-Type-Options"] = "nosniff"
    resp.headers["X-Frame-Options"] = "DENY"
    resp.headers["Cache-Control"] = "no-store"
    return resp

@app.route("/")
def raiz():
    return redirect(url_for("inicio" if g.usuario else "login"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if g.usuario:
        return redirect(url_for("inicio"))

    recordado = request.cookies.get(COOKIE_USUARIO, "")
    valores = {"usuario_valor": "", "recordar": False}

    if recordado:
        try:
            datos = _get_serializer().loads(recordado, max_age=60 * 60 * 24 * 30)
            valores["usuario_valor"] = datos.get("usuario", "")
            valores["recordar"] = True
        except (BadSignature, SignatureExpired):
            valores["usuario_valor"] = ""

    if request.method == "POST":
        nombre_usuario = request.form.get("usuario", "").strip()
        clave = request.form.get("clave", "")
        recordar = request.form.get("recordar") == "on"
        valores = {"usuario_valor": nombre_usuario, "recordar": recordar}

        if not nombre_usuario or not clave:
            flash("Escribe tu usuario y tu contraseña.", "error")
            return render_template("login.html", **valores), 400

        llave = (nombre_usuario.lower(), request.remote_addr)
        minutos = _bloqueado(llave)
        if minutos:
            flash(f"Demasiados intentos fallidos. Espera {minutos} min e inténtalo de nuevo.", "error")
            return render_template("login.html", **valores), 429

        fila = get_db().execute(
            "SELECT * FROM usuarios WHERE usuario = %s", (nombre_usuario,)
        ).fetchone()

        if fila is None or not check_password_hash(fila["clave_hash"], clave):
            _registrar_fallo(llave)
            flash("Usuario o contraseña incorrectos.", "error")
            return render_template("login.html", **valores), 401

        if not fila["activo"]:
            flash("Tu usuario está inactivo. Pide al administrador que lo active.", "error")
            return render_template("login.html", **valores), 403

        _intentos.pop(llave, None)
        session.clear()
        session["uid"] = fila["id"]

        resp = redirect(url_for("inicio"))
        if recordar:
            # RF-20 / RNF-08: credenciales guardadas firmadas (no en texto plano)
            token = _get_serializer().dumps({"usuario": fila["usuario"], "clave": clave})
            resp.set_cookie(COOKIE_USUARIO, token,
                            max_age=60 * 60 * 24 * 30,
                            httponly=True, samesite="Lax")
        else:
            resp.delete_cookie(COOKIE_USUARIO)
        return resp

    return render_template("login.html", **valores)


@app.route("/inicio")
@login_requerido
def inicio():
    ahora = datetime.now()
    saludo = ("Buenos días" if ahora.hour < 12
              else "Buenas tardes" if ahora.hour < 19 else "Buenas noches")
    fecha = f"{DIAS[ahora.weekday()].capitalize()} {ahora.day} de {MESES[ahora.month - 1]} de {ahora.year}"
    modulos = [
        {**m, "permitido": g.usuario["rol"] in m["roles"]} for m in MODULOS
    ]
    return render_template("inicio.html", saludo=saludo, fecha=fecha, modulos=modulos)


@app.route("/modulo/<slug>")
@login_requerido
def modulo(slug):
    datos = MODULOS_POR_SLUG.get(slug)
    if datos is None:
        abort(404)
    if g.usuario["rol"] not in datos["roles"]:
        abort(403)
    if slug == "configuracion":
        return redirect(url_for("configuracion.etiquetas"))
    return render_template("modulo.html", modulo=datos)


@app.route("/salir", methods=["POST"])
def salir():
    session.clear()
    return redirect(url_for("login"))


@app.errorhandler(403)
def sin_permiso(_e):
    return render_template("error.html", titulo="Sin acceso",
                           mensaje="Tu rol no tiene permiso para entrar a esta sección."), 403


@app.errorhandler(404)
def no_encontrado(_e):
    return render_template("error.html", titulo="Página no encontrada",
                           mensaje="La dirección no existe en Exodus Contable."), 404


@app.errorhandler(400)
def solicitud_invalida(_e):
    return render_template("error.html", titulo="Solicitud no válida",
                           mensaje="La sesión expiró o el formulario no es válido. Vuelve a intentarlo."), 400


iniciar_db()

if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=os.environ.get("EXODUS_DEBUG") == "1")