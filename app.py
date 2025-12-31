from flask import Flask, request, render_template, redirect, url_for
import json
import os

app = Flask(__name__)
DATA_FILE = "ncc_data.json"

# ---------------- DATA HANDLING ----------------

def load_data():
    if os.path.exists(DATA_FILE):
        with open(DATA_FILE, "r") as f:
            return json.load(f)
    return {"institutions": {}, "cadets": {}, "quizzes": []}

def save_data(data):
    with open(DATA_FILE, "w") as f:
        json.dump(data, f, indent=4)

data = load_data()

# ---------------- HOME ----------------

@app.route("/")
def home():
    return render_template("index.html")

@app.route("/choose_role", methods=["POST"])
def choose_role():
    role = request.form.get("role")
    if role == "institution":
        return redirect(url_for("institution_login"))
    elif role == "cadet":
        return redirect(url_for("cadet_login"))
    return redirect(url_for("home"))

# ---------------- INSTITUTION ----------------


@app.route("/institution/login", methods=["GET", "POST"])
def institution_login():
    if request.method == "POST":
        phone = request.form.get("phone")

        if phone in data["institutions"]:
            return redirect(url_for("institution_dashboard", phone=phone))
        else:
            return redirect(url_for("institution_register"))

    return render_template("institution_login.html")


@app.route("/institution/register", methods=["GET", "POST"])
def institution_register():
    if request.method == "POST":
        phone = request.form.get("phone")
        name = request.form.get("name")
        data["institutions"][phone] = {"name": name}
        save_data(data)
        return redirect(url_for("institution_dashboard", phone=phone))
    return render_template("institution_register.html")

@app.route("/institution/dashboard/<phone>")
def institution_dashboard(phone):
    institution = data["institutions"].get(phone)
    return render_template(
        "institution_dashboard.html",
        institution=institution,
        institution_phone=phone
    )

@app.route("/institution/create_quiz/<phone>", methods=["GET", "POST"])
def create_quiz_page(phone):
    if request.method == "POST":
        quiz_name = request.form.get("quiz_name")
        total = int(request.form.get("total"))

        questions, answers = [], []
        for i in range(1, total + 1):
            q = request.form.get(f"q{i}")
            a = request.form.get(f"a{i}").strip().lower()
            questions.append(q)
            answers.append(a)

        data["quizzes"].append({
            "institution": phone,
            "quiz_name": quiz_name,
            "questions": questions,
            "answers": answers
        })
        save_data(data)
        return redirect(url_for("institution_dashboard", phone=phone))

    return render_template("create_quiz.html", phone=phone)

# ---------------- CADET ----------------

@app.route("/cadet/login", methods=["GET"])
def cadet_login_page():
    return render_template("cadet_login.html")

@app.route("/cadet/login", methods=["POST"])
def cadet_login():
    phone = request.form.get("phone")
    if phone in data["cadets"]:
        return redirect(url_for("cadet_dashboard", phone=phone))
    return redirect(url_for("cadet_register_page"))

@app.route("/cadet/register", methods=["GET", "POST"])
def cadet_register_page():
    institutions = list(data["institutions"].values())
    if request.method == "POST":
        phone = request.form.get("phone")
        name = request.form.get("name")
        college = request.form.get("college")
        data["cadets"][phone] = {"name": name, "college": college, "scores": {}}
        save_data(data)
        return redirect(url_for("cadet_dashboard", phone=phone))
    return render_template("cadet_register.html", institutions=institutions)

@app.route("/cadet/dashboard/<phone>")
def cadet_dashboard(phone):
    cadet = data["cadets"].get(phone)
    return render_template("cadet_dashboard.html", cadet=cadet, cadet_phone=phone)

@app.route("/cadet/quizzes/<phone>")
def cadet_quizzes(phone):
    cadet = data["cadets"].get(phone)
    attempted = cadet["scores"].keys()
    available = [q for q in data["quizzes"] if q["quiz_name"] not in attempted]
    return render_template("cadet_quizzes.html", quizzes=available, cadet_phone=phone)

@app.route("/cadet/attempt/<phone>/<quiz_name>", methods=["GET", "POST"])
def attempt_quiz(phone, quiz_name):
    quiz = next(q for q in data["quizzes"] if q["quiz_name"] == quiz_name)
    if request.method == "POST":
        score = 0
        for i, correct in enumerate(quiz["answers"], start=1):
            user_ans = request.form.get(f"a{i}", "").strip().lower()
            if user_ans == correct:
                score += 1
        data["cadets"][phone]["scores"][quiz_name] = score
        save_data(data)
        return redirect(url_for("cadet_dashboard", phone=phone))
    return render_template("attempt_quiz.html", quiz=quiz, cadet_phone=phone)

# ---------------- LEADERBOARD ----------------

@app.route("/leaderboard")
def leaderboard():
    board = []
    for cadet in data["cadets"].values():
        board.append({
            "name": cadet["name"],
            "college": cadet["college"],
            "scores": cadet["scores"],
            "total": sum(cadet["scores"].values())
        })
    board.sort(key=lambda x: x["total"], reverse=True)
    return render_template("leaderboard.html", board=board)

# ---------------- RUN ----------------

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=10000,debug=True)
