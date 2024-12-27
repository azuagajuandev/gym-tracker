from flask import Flask, render_template, request, redirect
import sqlite3
import json
import os

app = Flask(__name__)

# Función para manejar conexiones
def get_db_connection():
    connection = sqlite3.connect("database.db")
    connection.row_factory = sqlite3.Row
    return connection

# Crear tabla si no existe
try:
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS entrenamientos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            fecha DATE NOT NULL,
            tipo_ejercicio VARCHAR(255) NOT NULL,
            series INTEGER NOT NULL,
            repeticiones INTEGER NOT NULL,
            peso INTEGER NOT NULL
        );
    """)
    con.commit()
    con.close()
    print("La tabla fue creada o conectada exitosamente.")
except sqlite3.Error as e:
    print(f"Error al crear o conectar la tabla: {e}")

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
@app.route("/")
def index():
    con = get_db_connection()
    cur = con.cursor()
    cur.execute("SELECT * FROM entrenamientos")
    entrenamientos_db = cur.fetchall()
    con.close()
    return render_template("index.html", entrenamientos=entrenamientos_db)

@app.route("/agregar", methods=["POST"])
def agregar():
    # Capturar datos del formulario
    fecha = request.form.get("fecha")
    ejercicio = request.form.get("ejercicio")
    series = request.form.get("series")
    repeticiones = request.form.get("repeticiones")
    peso = request.form.get("peso")

    # Validar los datos antes de insertarlos
    if not (fecha and ejercicio and series and repeticiones and peso):
        print("Faltan datos. No se puede insertar en la base de datos.")
        return redirect("/")

    try:
        # Conectar a la base de datos
        con = get_db_connection()
        cur = con.cursor()

        # Insertar los datos
        cur.execute("""
            INSERT INTO entrenamientos (fecha, tipo_ejercicio, series, repeticiones, peso)
            VALUES (?, ?, ?, ?, ?);
        """, (fecha, ejercicio, series, repeticiones, peso))

        # Confirmar los cambios
        con.commit()
        print("Datos insertados exitosamente.")

    except sqlite3.Error as e:
        print(f"Error al insertar datos en la base de datos: {e}")

    finally:
        # Cerrar la conexión
        if con:
            con.close()

    return redirect("/")

@app.route("/eliminar", methods=["POST"])
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
def rutina():
    return render_template("rutina.html", rutina_json=rutina_json)

if __name__ == '__main__':
    port = int(os.environ.get("PORT", 5000))  # Railway necesita usar el puerto definido por la variable de entorno
    app.run(host='0.0.0.0', port=port)