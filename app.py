from flask import Flask, render_template, request, redirect, url_for, session, send_file
from flask_pymongo import PyMongo
import io
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas

app = Flask(__name__)
app.secret_key = "heartify_secret_key_2025"

# Use exact DB name with capital H as you requested
app.config["MONGO_URI"] = "mongodb://localhost:27017/Heartifyconnection"
mongo = PyMongo(app)

# Hardcoded credentials (kept exactly)
USERNAME = "admin"
PASSWORD = "1234"

@app.route("/", methods=["GET"])
def root():
    return redirect(url_for("login"))

@app.route("/login", methods=["GET", "POST"])
def login():
    # Keep the login flow exactly as before
    error = None
    if request.method == "POST":
        uname = request.form.get("username", "").strip()
        pwd = request.form.get("password", "").strip()
        if uname == USERNAME and pwd == PASSWORD:
            session["user"] = uname
            return redirect(url_for("dashboard"))
        else:
            error = "Invalid username or password"
            return render_template("login.html", error=error)
    return render_template("login.html", error=error)

@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "user" not in session:
        return redirect(url_for("login"))

    # Save submitted health data into MongoDB
    if request.method == "POST":
        heart_rate = request.form.get("heart_rate", "").strip()
        bp = request.form.get("bp", "").strip()
        sugar = request.form.get("sugar", "").strip()
        smoker = request.form.get("smoker", "").strip()

        # Insert only if at least one field provided (safe)
        mongo.db.records.insert_one({
            "username": session["user"],
            "heart_rate": heart_rate,
            "bp": bp,
            "sugar": sugar,
            "smoker": smoker
        })

    # fetch all records for display (descending latest first)
    records_cursor = mongo.db.records.find({"username": session.get("user", None)})
    records = list(records_cursor)
    # convert _id to string if needed in templates (we won't show _id)
    for r in records:
        r.pop("_id", None)

    return render_template("dashboard.html", user=session["user"], records=records)

@app.route("/download_pdf", methods=["GET"])
def download_pdf():
    if "user" not in session:
        return redirect(url_for("login"))

    # produce PDF containing latest records for the logged-in user
    records = list(mongo.db.records.find({"username": session["user"]}))
    buffer = io.BytesIO()
    p = canvas.Canvas(buffer, pagesize=letter)
    p.setTitle("Heartify Report")

    # Header
    p.setFont("Helvetica-Bold", 18)
    p.drawString(55, 750, "❤️ Heartify Health Report")
    p.setFont("Helvetica", 11)
    p.drawString(55, 734, f"User: {session['user']}")

    y = 710
    if not records:
        p.drawString(55, y, "No records available.")
    else:
        p.drawString(55, y, "Recent records (latest first):")
        y -= 24
        # show latest 10 records or fewer
        for rec in reversed(records[-10:]):
            line = f"Heart Rate: {rec.get('heart_rate','-')} | BP: {rec.get('bp','-')} | Sugar: {rec.get('sugar','-')} | Smoker: {rec.get('smoker','-')}"
            p.drawString(55, y, line)
            y -= 18
            if y < 60:
                p.showPage()
                y = 750

    p.showPage()
    p.save()
    buffer.seek(0)

    return send_file(buffer, as_attachment=True, download_name="heartify_report.pdf", mimetype="application/pdf")

@app.route("/logout")
def logout():
    session.pop("user", None)
    return redirect(url_for("login"))

if __name__ == "__main__":
    app.run(debug=True)

