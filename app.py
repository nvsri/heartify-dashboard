from flask import Flask, render_template, request, redirect, url_for, session, jsonify
from flask_pymongo import PyMongo
from bson.objectid import ObjectId

app = Flask(__name__)
app.secret_key = "supersecretkey"

# MongoDB connection
app.config["MONGO_URI"] = "mongodb://localhost:27017/Heartifyconnection"
mongo = PyMongo(app)
users = mongo.db.users
health_data = mongo.db.health_data

# Home route → login page
@app.route("/")
def home():
    return redirect(url_for("login"))

# ---------------- Login ----------------
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = users.find_one({"username": username, "password": password})
        if user:
            session["user"] = username
            return redirect(url_for("dashboard"))
        else:
            return render_template("login.html", error="Invalid username or password")
    return render_template("login.html")

# ---------------- Registration ----------------
@app.route("/register", methods=["GET", "POST"])
def register():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        confirm_password = request.form["confirm_password"]

        if password != confirm_password:
            return render_template("register.html", error="Passwords do not match")

        if users.find_one({"username": username}):
            return render_template("register.html", error="Username already exists")

        users.insert_one({"username": username, "password": password})
        return redirect(url_for("login"))

    return render_template("register.html")

# ---------------- Dashboard ----------------
@app.route("/dashboard")
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    username = session["user"]
    records = list(health_data.find({"username": username}))
    return render_template("dashboard.html", username=username, records=records)

# ---------------- Submit health data ----------------
@app.route("/submit_health_data", methods=["POST"])
def submit_health_data():
    if "user" not in session:
        return redirect(url_for("login"))

    data = {
        "username": session["user"],
        "heart_rate": request.form["heart_rate"],
        "bp_level": request.form["bp_level"],
        "sugar_level": request.form["sugar_level"],
        "pulse_rate": request.form["pulse_rate"],
        "smoker_status": request.form["smoker_status"]
    }
    health_data.insert_one(data)
    return redirect(url_for("dashboard"))

# ---------------- Generate Report ----------------
@app.route("/generate_report", methods=["POST"])
def generate_report():
    if "user" not in session:
        return redirect(url_for("login"))
    # (Placeholder) In future, you can add PDF generation logic here
    return redirect(url_for("dashboard"))

# ---------------- Logout ----------------
@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

@app.route("/chatbot", methods=["POST"])
def chatbot():
    user_msg = (request.json or {}).get("message", "")
    text = user_msg.lower().strip()

    # Exact-match FAQ
    faq = {
        "what is heartify": "Heartify is your personal heart health tracker.",
        "how to save data": "Fill the health form and click Save Data.",
        "how to generate report": "Click the PDF button on the dashboard.",
        "hello": "Hello! How can I help you?",
        "hi": "Hi! What would you like to know?",
        "thanks": "You're welcome! Happy to help.",
        "thank you": "You're welcome!"
    }

    if text in faq:
        reply = faq[text]
    else:
        # Fuzzy / keyword matching for more interactive responses
        # Additional FAQ: heart care tips (check before generic 'heart' keyword)
        if "heart care tips" in text or "heart care" in text or "care tips" in text or text == "tips":
            reply = "No excessive sugar. Drink water. Proper sleep. Do exercise."
        elif any(k in text for k in ("save", "save data", "form", "health form")):
            reply = "To save data: fill the form fields (heart rate, BP, sugar, pulse, smoker) and click 'Save Data'."
        elif "report" in text or "pdf" in text or "download" in text:
            reply = "To generate a report, click the Download PDF button in the 'Generate Report' card on the left sidebar."
        elif any(k in text for k in ("symptom", "symptoms", "risk", "chance")):
            reply = "If you're worried about symptoms or risk of heart disease, consult a healthcare professional. I can help explain metrics like BP, sugar, and heart rate."
        elif "heart" in text or "heart rate" in text or "bpm" in text:
            reply = "Heart rate is measured in beats per minute (bpm). Normal resting heart rate for adults is roughly 60-100 bpm."
        elif "help" in text or "what can i ask" in text or "commands" in text:
            reply = "You can ask: 'what is heartify', 'how to save data', 'how to generate report', or ask about heart rate, blood pressure, and similar topics."
        else:
            reply = "Sorry, I don't have an answer for that. Try asking 'what is heartify' or 'how to save data'."

    return jsonify({"reply": reply})

# Run the app
if __name__ == "__main__":
    app.run(debug=True)













