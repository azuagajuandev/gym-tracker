from flask import Flask, render_template, request, redirect
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
import sqlite3
import json
import os

app = Flask(__name__)
app.secret_key = b')\x1f~\x1f\xb82m;\xcc@@\xc9\x8c\xf9\x054t\xa6\xa4D\xf5\x02\xe9w'

# Función para manejar conexiones
def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection

# Flask-Login configuration
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# User model
class User(UserMixin):
    def __init__(self, id, username):
        self.id = id
        self.username = username

# Crear tabla si no existe
try:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        );
    """)
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entrenamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            tipo_ejercicio VARCHAR(255) NOT NULL,
            series INTEGER NOT NULL,
            repeticiones INTEGER NOT NULL,
            peso INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (id)
        );
    """)
    con.commit()
    con.close()
    print("La tabla fue creada o conectada exitosamente.")
except sqlite3.Error as e:
    print(f"Error al crear o conectar la tabla: {e}")

# Crear usuarios iniciales si no existen
try:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT COUNT(*) FROM users")
    user_count = cur.fetchone()[0]  # Verifica si hay usuarios en la tabla
    if user_count == 0:  # Si no hay usuarios, crea los iniciales
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("juan", "1234"))
        cur.execute("INSERT INTO users (username, password) VALUES (?, ?)", ("marcio", "1234"))
        con.commit()
        print("Usuarios iniciales creados.")  # Mensaje si los usuarios son creados
    else:
        print("Usuarios ya existentes. No se crean nuevos.")  # Mensaje si los usuarios ya existen
    con.close()
except sqlite3.Error as e:
    print(f"Error al crear usuarios iniciales: {e}")

# Leer JSON
json_file_path = "static/rutina.json"
try:
    with open(json_file_path, "r") as file:
        rutina_json = json.load(file)
    print("Archivo JSON cargado exitosamente.")
except FileNotFoundError:
    rutina_json = []
    print(f"Archivo '{json_file_path}' no encontrado. Lista vacía cargada.")
except json.JSONDecodeError:
    rutina_json = []
    print(f"Error al decodificar el archivo JSON. Lista vacía cargada.")

# Rutas

@login_manager.user_loader
def load_user(user_id):
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM users WHERE id = ?", (user_id,))
    user_row = cur.fetchone()
    con.close()
    if user_row:
        return User(user_row["id"], user_row["username"])
    return None

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form.get("username")
        password = request.form.get("password")

        # Verificar credenciales
        con = get_db_connection()
        cur = con.cursor()
        cur.execute("SELECT * FROM users WHERE username = ? AND password = ?", (username, password))
        user_row = cur.fetchone()
        con.close()

        if user_row:
            user = User(user_row["id"], user_row["username"])
            login_user(user)
            return redirect("/")
        else:
            return "Credenciales inválidas, intente nuevamente.", 401

    return render_template("login.html")

@app.route("/logout")
@login_required
def logout():
    logout_user()
    return redirect("/login")

@app.route("/")
@login_required
def index():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM entrenamientos WHERE user_id = ?", (current_user.id,))
    entrenamientos_db = cur.fetchall()
    con.close()
    return render_template("index.html", entrenamientos=entrenamientos_db)

@app.route("/agregar", methods=["POST"])
@login_required
def agregar():
    fecha = request.form.get("fecha")
    ejercicio = request.form.get("ejercicio")
    series = request.form.get("series")
    repeticiones = request.form.get("repeticiones")
    peso = request.form.get("peso")

    if not (fecha and ejercicio and series and repeticiones and peso):
        print("Faltan datos. No se puede insertar en la base de datos.")
        return redirect("/")

    try:
        con = get_db_connection()
        cur = con.cursor()
        cur.execute("""
            INSERT INTO entrenamientos (fecha, tipo_ejercicio, series, repeticiones, peso, user_id)
            VALUES (?, ?, ?, ?, ?, ?);
        """, (fecha, ejercicio, series, repeticiones, peso, current_user.id))
        con.commit()
        print("Datos insertados exitosamente.")
    except sqlite3.Error as e:
        print(f"Error al insertar datos en la base de datos: {e}")
    finally:
        if con:
            con.close()

    return redirect("/")

@app.route("/eliminar", methods=["POST"])
@login_required
def borrar():
    id = request.form.get("id")

    try:
        # Conectar a la base de datos
        con = get_db_connection()
        cur = con.cursor()

        # Insertar los datos
        cur.execute("DELETE FROM entrenamientos WHERE id = ?;", (id,))

        # Confirmar los cambios
        con.commit()
        print("Datos eliminados exitosamente.")

    except sqlite3.Error as e:
        print(f"Error al insertar datos en la base de datos: {e}")

    finally:
        # Cerrar la conexión
        if con:
            con.close()

    return redirect("/")

@app.route("/rutina")
@login_required
def rutina():
    return render_template("rutina.html", rutina_json=rutina_json)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Railway necesita usar el puerto definido por la variable de entorno
    app.run(host='0.0.0.0', port=port)