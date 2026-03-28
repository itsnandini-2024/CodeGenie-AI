from flask import Flask, render_template, request, redirect, url_for
from groq import Groq
import sqlite3
from datetime import datetime
from flask import redirect, url_for
import os

ADMIN_USERNAME = "admin"
ADMIN_PASSWORD = "admin123"
app = Flask(__name__)



@app.route("/logout")
def logout():
    return redirect(url_for("login"))

# ================== GROQ SETUP ==================
# 🔴 Replace with your API key
client = Groq(api_key="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")

# ================== DATABASE SETUP ==================
def init_db():
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
            CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
           username TEXT UNIQUE,
            password TEXT
)
""")
    


    cursor.execute("""
        CREATE TABLE IF NOT EXISTS history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            username TEXT,
            language TEXT,
            prompt TEXT,
            code TEXT,
            explanation TEXT,
            example TEXT,
            date TEXT
        )
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS feedback(
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT,
        prompt TEXT,
        message TEXT
)
""")

    

    conn.commit()
    conn.close()

init_db()

# ================== LOGIN ==================
@app.route("/", methods=["GET","POST"])
def login():

    if request.method == "POST":

        username = request.form["username"]
        password = request.form["password"]

        # ADMIN LOGIN
        if username == ADMIN_USERNAME and password == ADMIN_PASSWORD:
            return redirect("/admin/dashboard")

        # NORMAL USER LOGIN
        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT OR IGNORE INTO users (username,password) VALUES (?,?)",
            (username, password)
        )

        conn.commit()
        conn.close()

        return redirect(f"/home/{username}")

    return render_template("login.html")


# ================== HOME ==================
@app.route("/home/<username>")
def home(username):
    return render_template("home.html", username=username)


# ================== GENERATE ==================
@app.route("/generate/<username>", methods=["GET","POST"])
def generate(username):

    language = request.form.get("language")
    prompt = request.form.get("prompt")

    system_prompt = f"""
You are a professional coding assistant.

Respond STRICTLY in this format:

===CODE===
<only code>

===EXPLANATION===
<numbered step by step explanation>

===EXAMPLE===
Input:
...
Expected Output:
...
Explanation:
...
"""

    response = client.chat.completions.create(
        model="llama-3.1-8b-instant",  # ✅ working model
        messages=[
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Language: {language}\nProblem: {prompt}"}
        ],
        temperature=0.3
    )

    full_response = response.choices[0].message.content
    
    # ================== SPLIT RESPONSE ==================
    code_part = ""
    explanation_part = ""
    example_part = ""

    if "===CODE===" in full_response:
        parts = full_response.split("===CODE===")[1]
        if "===EXPLANATION===" in parts:
            code_part = parts.split("===EXPLANATION===")[0].strip()
            rest = parts.split("===EXPLANATION===")[1]

            if "===EXAMPLE===" in rest:
                explanation_part = rest.split("===EXAMPLE===")[0].strip()
                example_part = rest.split("===EXAMPLE===")[1].strip()

    # ================== SAVE TO DATABASE ==================
    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO history (username, language, prompt, code, explanation, example, date)
        VALUES (?, ?, ?, ?, ?, ?, ?)
    """, (
        username,
        language,
        prompt,
        code_part,
        explanation_part,
        example_part,
        datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    ))

    conn.commit()
    conn.close()

    return render_template(
        "home.html",
        username=username,
        selected_language=language,
        code=code_part,
        explanation=explanation_part,
        example=example_part,
        prompt=prompt
    )


# ================== HISTORY ==================
@app.route("/history/<username>")
def history(username):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("""
        SELECT language, prompt, code, explanation, example, date
        FROM history
        WHERE username=?
        ORDER BY id DESC
    """, (username,))

    records = cursor.fetchall()
    conn.close()

    return render_template(
        "history.html",
        username=username,
        records=records
    )
@app.route("/dashboard/<username>")
def dashboard(username):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    # Total prompts
    cursor.execute("""
        SELECT COUNT(*) FROM history WHERE username=?
    """, (username,))
    total = cursor.fetchone()[0]

    # Most used language
    cursor.execute("""
        SELECT language, COUNT(language) as count
        FROM history
        WHERE username=?
        GROUP BY language
        ORDER BY count DESC
        LIMIT 1
    """, (username,))
    
    result = cursor.fetchone()
    most_used = result[0] if result else "None"

    # Language usage breakdown
    cursor.execute("""
        SELECT language, COUNT(language)
        FROM history
        WHERE username=?
        GROUP BY language
    """, (username,))
    
    language_stats = cursor.fetchall()

    # Last activity
    cursor.execute("""
        SELECT date FROM history
        WHERE username=?
        ORDER BY id DESC
        LIMIT 1
    """, (username,))
    
    last = cursor.fetchone()
    last_activity = last[0] if last else "No activity"

    conn.close()

    return render_template(
        "dashboard.html",
        username=username,
        total=total,
        most_used=most_used,
        last_activity=last_activity,
        language_stats=language_stats
    )
@app.route("/admin/dashboard")
def admin_dashboard():



    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()
    

    cursor.execute("SELECT COUNT(*) FROM users")
    total_users = cursor.fetchone()[0]
    # Get all users
    cursor.execute("SELECT username FROM users")
    users = cursor.fetchall()

    # Get history logs
    cursor.execute("SELECT username, language, prompt, date FROM history")
    history = cursor.fetchall()

    # Get feedback messages
    cursor.execute("SELECT username,prompt, message FROM feedback")
    feedbacks = cursor.fetchall()

    cursor.execute("""
                   SELECT language, COUNT(*) 
       FROM history 
       GROUP BY language
       """)


    language_stats = cursor.fetchall() 
     
     
    languages = [row[0] for row in language_stats]
    counts = [row[1] for row in language_stats]
     
        

    return render_template(
        "admin_dashboard.html",
        users=users,
        history=history,
        feedbacks=feedbacks,
        total_users=total_users,
        languages=languages,
        counts=counts
    ) 

@app.route("/admin/user/<username>")
def admin_user(username):

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT language, prompt, date FROM history WHERE username=?", (username,))
    history = cursor.fetchall()

    cursor.execute("SELECT prompt, message FROM feedback WHERE username=?", (username,))
    feedbacks = cursor.fetchall()

    conn.close()

    return render_template(
        "admin_user.html",
        username=username,
        history=history,
        feedbacks=feedbacks
    )
@app.route("/feedback/<username>", methods=["GET","POST"])
def feedback(username):

    if request.method == "POST":

        message = request.form.get("message")
        prompt = request.form.get("prompt")

        conn = sqlite3.connect("database.db")
        cursor = conn.cursor()

        cursor.execute(
            "INSERT INTO feedback (username,prompt,message) VALUES (?,?,?)",
            (username, prompt, message)
        )

        conn.commit()
        conn.close()

        return redirect(f"/generate/{username}")

    return redirect(f"/generate/{username}")
        
                                        
                                        
    

@app.route("/admin")
def admin_panel():
    return render_template("admin_panel.html")

@app.route("/admin/feedback")
def admin_feedback():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username,message FROM feedback")

    data = cursor.fetchall()

    conn.close()

    return render_template("admin_feedback.html", data=data)

@app.route("/admin/history")
def admin_history():

    conn = sqlite3.connect("database.db")
    cursor = conn.cursor()

    cursor.execute("SELECT username, language, prompt, date FROM history ORDER BY id DESC")

    records = cursor.fetchall()

    conn.close()

    return render_template("admin_history.html", records=records)

# ================== RUN APP ==================
if __name__ == "__main__":
    init_db()
    app.run(debug=True)