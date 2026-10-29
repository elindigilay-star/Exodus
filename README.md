# EXODUS Contable

Aplicación web integral para la administración, inventario, nómina y
contabilidad de PYMES. Todo el proyecto se ejecuta desde **un solo punto de
entrada** (`run.py`), con **una sola base de datos MySQL/MariaDB** y **un solo
sistema de usuarios**.

---

## 1. Requisitos

- Python 3.10 o superior
- MySQL 8.x o MariaDB 10.4 o superior (encendido)
- Windows, Linux o macOS

Dependencias de Python (se instalan solas con `iniciar.bat`):

```
Flask, PyMySQL, openpyxl, reportlab
```

---

## 2. Instalación rápida (Windows)

1. Instala Python desde <https://www.python.org/downloads/> marcando
   **“Add Python to PATH”**.
2. Enciende MySQL/MariaDB (XAMPP, WAMP, HeidiSQL, servicio de Windows, etc.).
3. Haz doble clic en **`iniciar.bat`**.

El archivo crea el entorno virtual `.venv`, instala las dependencias y arranca
la aplicación en <http://127.0.0.1:5000>.

### Instalación manual

```bat
cd C:\ruta\a\EXODUS
py -3 -m venv .venv
.venv\Scripts\activate
pip install -r requirements.txt
python run.py
```

En Linux/macOS:

```bash
cd /ruta/a/EXODUS
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
python run.py
```

---

## 3. Base de datos

La aplicación usa **una única base** llamada `sistema_contable`.

Al arrancar, `Modulo-contable/database/init_db.py`:

1. crea la base si no existe;
2. aplica el esquema completo de `Modulo-contable/sistema_contable.sql`
   (es idempotente: **no borra datos**);
3. agrega columnas nuevas a bases creadas con versiones anteriores;
4. crea usuarios de demostración solo si la tabla `usuarios` está vacía y
   `EXODUS_DEMO` no es `0`.

También puedes importar el `.sql` manualmente desde phpMyAdmin o HeidiSQL.

### Configuración por variables de entorno

No hace falta editar el código. En Windows (CMD):

```bat
set EXODUS_DB_HOST=127.0.0.1
set EXODUS_DB_PORT=3306
set EXODUS_DB_USER=exodus
set EXODUS_DB_PASSWORD=mi_clave
set EXODUS_DB_NAME=sistema_contable
python run.py
```

| Variable            | Por defecto        | Descripción                              |
|---------------------|--------------------|------------------------------------------|
| `EXODUS_DB_HOST`    | `127.0.0.1`        | Servidor MySQL/MariaDB                   |
| `EXODUS_DB_PORT`    | `3306`             | Puerto                                   |
| `EXODUS_DB_USER`    | `root`             | Usuario de la base                       |
| `EXODUS_DB_PASSWORD`| *(vacío)*          | Contraseña                               |
| `EXODUS_DB_NAME`    | `sistema_contable` | Nombre de la base única                  |
| `EXODUS_SECRET_KEY` | archivo generado   | Clave de sesión (si no, `instance/secret_key`) |
| `EXODUS_DEBUG`      | `0`                | `1` activa el depurador (solo desarrollo)|
| `EXODUS_HOST`       | `127.0.0.1`        | Host de la aplicación                    |
| `EXODUS_PORT`       | `5000`             | Puerto de la aplicación                  |
| `EXODUS_DEMO`       | `1`                | `0` evita crear usuarios de demostración |

> **Recomendado para producción:** crea un usuario MySQL propio (no `root`),
> define `EXODUS_DEMO=0`, usa una contraseña fuerte y deja `EXODUS_DEBUG` sin
> activar.

---

## 4. Ejecución

```bat
python run.py
```

Opciones útiles:

```bat
python run.py --host 0.0.0.0 --port 5000
python run.py --debug
```

### Crear un administrador sin usuarios de demostración

```bat
set EXODUS_DEMO=0
python run.py --crear-admin admin "MiClaveSegura" --nombre "Administrador Principal"
```

---

## 5. Usuarios de demostración

Solo se crean en una base vacía. **Cámbialos o bórralos antes de una entrega
real.**

| Usuario    | Contraseña    | Rol             |
|------------|---------------|-----------------|
| `admin`    | `admin123`    | Administrador   |
| `carlos`   | `carlos123`   | Administrador   |
| `contador` | `contador123` | Contador        |
| `ana`      | `ana123`      | Contador        |
| `auxiliar` | `auxiliar123` | Auxiliar        |
| `juan`     | `juan123`     | Auxiliar        |

El rol **Recursos Humanos** también existe (gestión de nómina y empleados) y se
puede asignar desde Configuración > Usuarios.

### Acceso por rol

| Rol                 | Inicio | Contabilidad | Inventario | Nómina | Configuración          |
|---------------------|:------:|:------------:|:----------:|:------:|:----------------------:|
| Administrador       | ✔      | ✔            | ✔          | ✔      | Todo                   |
| Contador            | ✔      | ✔            | ✔          | —      | Etiquetas y parámetros |
| Auxiliar            | ✔      | —            | ✔          | —      | —                      |
| Recursos Humanos    | ✔      | —            | —          | ✔      | —                      |
| Empleado            | ✔      | —            | —          | —      | —                      |

---

## 6. Módulos y direcciones

| Módulo            | Dirección                                  |
|-------------------|--------------------------------------------|
| Inicio / login    | `/` y `/login`                             |
| Contabilidad      | `/api/contabilidad/...`                    |
| Inventario        | `/api/inventario/modulo`                   |
| Nómina            | `/api/nomina/modulo`                       |
| Etiquetas         | `/configuracion/etiquetas`                 |
| Parámetros        | `/configuracion/parametros`                |
| Roles y permisos  | `/configuracion/roles`                     |
| Usuarios          | `/configuracion/usuarios`                  |

Todas las rutas `/api/` exigen sesión iniciada (responden `401` en JSON si no
la hay). Las escrituras de la API solo aceptan `Content-Type:
application/json`.

---

## 7. Estructura del proyecto

```
EXODUS/
├── run.py                     ← ÚNICO punto de entrada
├── iniciar.bat                ← instalación + arranque en Windows
├── requirements.txt
├── README.md
├── docs/
│   └── Especificacion_Requisitos.md
├── Modulo-contable/           ← aplicación principal (Flask)
│   ├── app.py                 ← fábrica crear_app()
│   ├── config.py              ← configuración central
│   ├── sistema_contable.sql   ← esquema completo de la base única
│   ├── database/              ← conexión e inicialización
│   ├── models/                ← acceso a datos
│   ├── routes/                ← login, contabilidad
│   ├── services/              ← lógica contable y reportes
│   ├── templates/ y static/
├── modulo-inventario/         ← módulo Python registrado en la app
├── modulo-nomina/
│   └── nomina/                ← módulo Python registrado en la app
└── modulo-configuracion/      ← usuarios, roles, etiquetas, parámetros
```

---

## 8. Seguridad aplicada

- Rutas `/api/` protegidas con sesión y rol; responden `401`/`403` en JSON.
- Clave de sesión fuera del código: `instance/secret_key` o
  `EXODUS_SECRET_KEY`.
- “Recordarme” guarda **solo el nombre de usuario**, nunca la contraseña.
- Bloqueo por intentos fallidos persistido en la tabla `intentos_login`.
- CSRF en formularios HTML y exigencia de JSON en las escrituras de la API.
- `debug` desactivado por defecto (`EXODUS_DEBUG=1` para desarrollo).
- Cabeceras `X-Frame-Options`, `X-Content-Type-Options`,
  `Referrer-Policy` y `Cache-Control: no-store`.
- Consultas SQL parametrizadas.

---

## 9. Problemas frecuentes

**`TemplateNotFound: login.html`**
Ocurría al ejecutar `routes/auth.py` como si fuera la aplicación principal.
Ahora hay que arrancar desde la raíz con `python run.py` (o `iniciar.bat`).
`Modulo-contable/app.py` fija las carpetas `templates` y `static` con rutas
absolutas, así que también funciona desde cualquier directorio.

**`Can't connect to MySQL server`**
MySQL/MariaDB está apagado o las credenciales son distintas. Revisa las
variables `EXODUS_DB_*`. La aplicación arranca igual y muestra el login, pero
no podrá consultar datos.

**`Access denied for user 'root'@'localhost'`**
Tu MySQL tiene contraseña. Define `EXODUS_DB_PASSWORD` o crea un usuario para
la aplicación.

**Puerto 5000 ocupado**
```bat
python run.py --port 5001
```

---

## 10. Documentación

La especificación de requisitos completa (RF-01 a RF-20, casos de uso,
diagramas y conclusiones) está en
[`docs/Especificacion_Requisitos.md`](docs/Especificacion_Requisitos.md).
