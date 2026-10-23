import pymysql
from pymysql.cursors import DictCursor

def obtener_conexion():
    """Establece y retorna una conexión activa a la base de datos MySQL."""
    return pymysql.connect(
        host='localhost',
        user='root',         # Cambia por tu usuario de MySQL
        password='',         # Cambia por tu contraseña de MySQL
        database='sistema_contable',
        cursorclass=DictCursor
    )