from flask import Flask, render_template, url_for, session, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
import requests

app = Flask(__name__)
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///users.db"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
db = SQLAlchemy(app)
app.secret_key = "very_unsecure_secret_key"


# Database Model
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(50), unique=True, nullable=False)
    password_hash = db.Column(db.String(300), nullable=False)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password, "pbkdf2:sha256")

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)


# ROUTES /***

@app.route("/")
def home():
    is_in_session = False
    if "username" in session:
        is_in_session = True
    return render_template("homepage.html", pagename="Home", isInSession=is_in_session)


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        password = request.form["password"]

        user = User.query.filter_by(username=username).first()
        if user and user.check_password(password):
            session["username"] = username
            return redirect(url_for("dashboard", username=session["username"]))
        else:
            return render_template("login.html", pagename="Login", error="Invalid username or password!")
    return render_template("login.html", pagename="Login")


@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        username = request.form['username']
        password = request.form['password']

        if User.query.filter_by(username=username).first():
            return render_template("signup.html", pagename="Sign Up", error="This user is already registered!")

        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()

        session["username"] = username

        return redirect(url_for("dashboard", username=session["username"]))
    return render_template("signup.html", pagename="Sign Up")


@app.route("/logout")
def logout():
    if "username" in session:
        session.pop("username")
        return redirect(url_for("home"))
    else:
        return redirect(url_for("home"))


@app.route("/dashboard")
def dashboard():
    is_in_session = False
    if "username" in session:
        username = session["username"]
        is_in_session = True
    else:
        return redirect(url_for("home"))
    url = "https://api.themoviedb.org/3/discover/movie?primary_release_year=2000"
    headers = {
        "accept": "application/json",
        "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5MWVhNjI5MWJjYjA0MjVlYTRiZWJmMTNmOTcyOTVlMiIsIm5iZiI6MTc1MzI5NDQzOS44MjA5OTk5LCJzdWIiOiI2ODgxMjY2NzZhMzgwNGMyMGUxNmFmZDAiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.5xA_CIxcW_VCkJPl-NrOyEUobnBwndzWmrhijGVc62o"
    }
    response = requests.get(url, headers=headers)
    return render_template("dashboard.html", pagename="Dashboard", username=username, isInSession=is_in_session, api_data=response.text)


@app.route("/movies")
def search_movies():
    if "username" in session:
        return render_template("movies.html")
    else:
        return redirect(url_for("home"))
    

@app.route("/tvshows")
def search_tvshows():
    if "username" in session:
        return render_template("tvshows.html")
    else:
        return redirect(url_for("home"))
    

@app.route("/all-tv")
def search_all():
    if "username" in session:
        return render_template("all-tv.html")
    else:
        return redirect(url_for("home"))


@app.errorhandler(404)
def invalid_route(e):
    is_in_session = False
    if "username" in session:
        is_in_session = True
    return render_template("error-page.html", isInSession=is_in_session)

# ***/


if __name__ == "__main__":
    with app.app_context():
        db.create_all()
    app.run(debug=True)
