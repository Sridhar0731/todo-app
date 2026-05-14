from flask import Flask, jsonify, request, render_template, session, redirect, url_for
import sqlite3
from flask_bcrypt import Bcrypt

def init_db():
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tasks (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            done BOOLEAN DEFAULT 0
        )
    """)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT NOT NULL UNIQUE,
            password TEXT NOT NULL
        )
    """)
    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN priority TEXT DEFAULT 'medium'")
        conn.commit()
    except:
        pass

    try: 
        cursor.execute("ALTER TABLE tasks ADD COLUMN user_id INTEGER")
        conn.commit()
    except:
        pass    

    try:
        cursor.execute("ALTER TABLE tasks ADD COLUMN due_date TEXT")
        conn.commit()
    except:
        pass

    conn.commit()
    conn.close()

init_db()   

app = Flask(__name__)
app.secret_key = "your_secret_key_123"
app.config["SESSION_COOKIE_SAMESITE"] = "Lax"
app.config["SESSION_COOKIE_SECURE"] = False
bcrypt = Bcrypt(app)

@app.route("/about")
def about():
    return "This is about page!"
@app.route("/tasks")
def get_tasks():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"message": "Not Logged in"}), 401
    
    conn =  sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks WHERE user_id = ?", (user_id,))
    rows = cursor.fetchall()
    conn.close()

    tasks = []
    for row in rows:
        tasks.append({
            "id" : row[0],
            "title" : row[1],
            "done" : row[2],
            "priority": row[3],
            "due_date": row[5]
        })

    return jsonify(tasks)

@app.route("/tasks", methods = ["POST"])
def add_task():
    user_id = get_current_user()
    if not user_id:
        return jsonify({"message": "Not Logged in!"}), 401
    
    data = request.get_json()
    title = data["title"]
    priority = data.get("priority", "medium")
    due_date = data.get("due_date", None)

    conn=sqlite3.connect("tasks.db")
    cursor=conn.cursor()
    cursor.execute("INSERT INTO tasks (title, priority, user_id, due_date) VALUES (?, ?, ?, ?)", (title, priority, user_id, due_date))
    conn.commit()
    conn.close

    return jsonify({"message" : "Task added!"})

@app.route("/tasks/<int:id>", methods=["DELETE"])
def delete_task(id):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tasks WHERE id = ?" , (id,))
    conn.commit()
    conn.close()

    return jsonify({"message" : "Task deleted!"})

@app.route("/tasks/<int:id>", methods=["PUT"])
def complete_task(id):
    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET done = 1 WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return jsonify({"message" : "Task marked as done!"})

@app.route("/tasks/<int:id>/rename", methods = ["PUT"])
def changetask_name(id):
    data=request.get_json()
    title= data["title"]
    conn=sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("UPDATE tasks SET title = ? WHERE id= ?", (title,id))
    conn.commit()
    conn.close()

    return jsonify({"message" : "Task name succesfully updated"}) 

def get_current_user():
    return session.get("user_id")

@app.route("/register", methods=["POST"])
def register():
    data = request.get_json()
    username = data["username"]
    password = bcrypt.generate_password_hash(data["password"]).decode("utf-8")

    try:
        conn = sqlite3.connect("tasks.db")
        cursor = conn.cursor()
        cursor.execute("INSERT INTO users (username, password) VALUES (?, ?)", (username, password))
        conn.commit()
        conn.close()
        return jsonify({"message": "Account created!"})
    except:
        return jsonify({"error": "Username already exists!"}), 400
    
@app.route("/login", methods = ["POST"])
def login():
    data = request.get_json()
    username = data["username"]
    password = data["password"]

    conn = sqlite3.connect("tasks.db")
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()

    if user and bcrypt.check_password_hash(user[2], password):
        session["user_id"] = user[0]
        session["username"] = user[1]
        return jsonify({"message": "Logged in!"})
    else:
        return jsonify({"error": "Invalid username or password!"}), 401
    
@app.route("/logout", methods = ["POST"])
def logout():
    session.clear()
    return jsonify({"message": "Logged out"})

@app.route("/")
def greet():
    if not get_current_user():
        return redirect(url_for("login_page"))
    return render_template("index.html")

@app.route("/login-page")
def login_page():
    return render_template("login.html")

if __name__=="__main__":
    app.run(debug=True)

