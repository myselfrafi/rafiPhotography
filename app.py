from flask import Flask, render_template, request, redirect, url_for, session, flash
import os
import pandas as pd

app = Flask(__name__)
app.secret_key = "ajay123"

# Paths for data storage
USER_DATA_PATH = "data/users.csv"
LEADERBOARD_PATH = "data/leaderboard.csv"

# Ensure directories and files exist
os.makedirs("data", exist_ok=True)
if not os.path.exists(USER_DATA_PATH):
    pd.DataFrame(columns=["username", "password"]).to_csv(USER_DATA_PATH, index=False)
if not os.path.exists(LEADERBOARD_PATH):
    pd.DataFrame(columns=["username", "category", "score"]).to_csv(LEADERBOARD_PATH, index=False)

def predict_image_quality(image_path):
    """Temporary function that returns a default score"""
    return 7.5

# Home route (login/register)
@app.route("/", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]
        action = request.form["action"]
        users = pd.read_csv(USER_DATA_PATH)

        if action == "Login":
            if (users["username"] == username).any() and (users[users["username"] == username]["password"].values[0] == password):
                session["username"] = username
                return redirect(url_for("dashboard"))
            else:
                flash("Invalid credentials. Please try again.")
        elif action == "Register":
            if (users["username"] == username).any():
                flash("Username already exists. Please choose another.")
            else:
                new_user = pd.DataFrame([[username, password]], columns=["username", "password"])
                new_user.to_csv(USER_DATA_PATH, mode="a", header=False, index=False)
                flash("Registration successful! You can now log in.")
    return render_template("login.html")


@app.route("/dashboard", methods=["GET", "POST"])
def dashboard():
    if "username" not in session:
        return redirect(url_for("login"))

    # Load the leaderboard CSV
    leaderboard = pd.read_csv(LEADERBOARD_PATH)

    # Identify the top scorer in each category
    categories = ["Wildlife photography", "Wedding photography", "Fashion photography"]
    winners = {}
    for category in categories:
        top_entry = leaderboard[leaderboard["category"] == category].sort_values(by="score", ascending=False).iloc[0]
        winners[category] = {
            "username": top_entry["username"],
            "score": top_entry["score"]
        }

    if request.method == "POST":
        category = request.form["category"]
        session["category"] = category
        return redirect(url_for("upload"))

    return render_template("dashboard.html", username=session["username"], winners=winners)

# Upload route
@app.route("/upload", methods=["GET", "POST"])
def upload():
    if "username" not in session:
        return redirect(url_for("login"))

    if request.method == "POST":
        if "image" not in request.files or not request.files["image"].filename:
            flash("No file uploaded.")
            return redirect(request.url)

        image = request.files["image"]
        image_path = os.path.join("uploads", image.filename)
        os.makedirs("uploads", exist_ok=True)
        image.save(image_path)

        # Process image (placeholder for prediction logic)
        score = predict_image_quality(image_path)

        # Save to leaderboard
        leaderboard = pd.read_csv(LEADERBOARD_PATH)
        new_entry = pd.DataFrame(
            [[session["username"], session["category"], score]],
            columns=["username", "category", "score"]
        )
        leaderboard = pd.concat([leaderboard, new_entry], ignore_index=True)
        leaderboard = leaderboard.sort_values(by="score", ascending=False).reset_index(drop=True)
        leaderboard.to_csv(LEADERBOARD_PATH, index=False)

        # Filter leaderboard by user's category
        filtered_leaderboard = leaderboard[leaderboard["category"] == session["category"]]

        return render_template(
            "result.html",
            username=session["username"],
            category=session["category"],
            score=score,
            leaderboard=filtered_leaderboard
        )

    return render_template("upload.html")

# Logout route
@app.route("/logout")
def logout():
    session.clear()
    return redirect(url_for('login'))

@app.route("/thank_you")
def thank_you():
    return render_template("thank_you.html")

if __name__ == "__main__":
    app.run(debug=True)
