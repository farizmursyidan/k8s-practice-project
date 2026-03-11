from flask import Flask, jsonify
import os
import psycopg2

app = Flask(__name__)

def get_connection():
    return psycopg2.connect(
        host=os.getenv("DB_HOST", "postgres-service"),
        database=os.getenv("DB_NAME", "mydb"),
        user=os.getenv("DB_USER", "myuser"),
        password=os.getenv("DB_PASSWORD", "mypassword")
    )

@app.route("/")
def home():
    return {"message": "Hello from Kubernetes backend"}

@app.route("/healthz")
def healthz():
    return jsonify({"status": "ok"}), 200

@app.route("/readyz")
def readyz():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT 1;")
        cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "ready"}), 200
    except Exception as e:
        return jsonify({"status": "not ready", "message": str(e)}), 500

@app.route("/db-check")
def db_check():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT version();")
        version = cur.fetchone()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "db_version": version[0]})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/init-db")
def init_db():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("""
            CREATE TABLE IF NOT EXISTS visitors (
                id SERIAL PRIMARY KEY,
                name TEXT NOT NULL
            );
        """)
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "message": "Table created"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/add-visitor/<name>")
def add_visitor(name):
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("INSERT INTO visitors (name) VALUES (%s);", (name,))
        conn.commit()
        cur.close()
        conn.close()
        return jsonify({"status": "success", "message": f"Added {name}"})
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

@app.route("/visitors")
def visitors():
    try:
        conn = get_connection()
        cur = conn.cursor()
        cur.execute("SELECT id, name FROM visitors ORDER BY id;")
        rows = cur.fetchall()
        cur.close()
        conn.close()
        return jsonify({
            "status": "success",
            "data": [{"id": r[0], "name": r[1]} for r in rows]
        })
    except Exception as e:
        return jsonify({"status": "error", "message": str(e)}), 500

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)