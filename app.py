from flask import Flask, render_template, url_for, session, redirect, request
from werkzeug.security import generate_password_hash, check_password_hash
from flask_sqlalchemy import SQLAlchemy
from random import randint
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


""" Home route """
# Sends the user to the homepage.
@app.route("/")
def home():
    # Check if user is logged in
    username_in_session = False
    if "username" in session:
        username_in_session = True
    return render_template("homepage.html", logged_in=username_in_session)


""" Signup route """
# Creates a new user and add them to the database.
# Sends the user to their dashboard page.
@app.route("/signup", methods=["GET", "POST"])
def signup():
    if request.method == "POST":
        # Store user form input
        username = request.form['username']
        password = request.form['password']

        # Signup validation
        error_message = signup_validation(username, password)
        if error_message:
            return render_template("signup.html", error=error_message)

        # Create new user and set their password
        new_user = User(username=username)
        new_user.set_password(password)
        # Add the user to the database
        db.session.add(new_user)
        db.session.commit()

        # Allow user to access dashboard
        session["username"] = username  # store session variable
        return redirect(url_for("dashboard", username=session["username"]))
    
    return render_template("signup.html")

def signup_validation(username, password):
    if username == '' and password == '':
        return "Username and Password cannot be empty"
    elif username == '':
        return "Username cannot be empty"
    elif password == '':
        return "Password cannot be empty"
    # Return None if there is no error with input
    else:
        return None


""" Login route """
# Logs the user in by creating a session variable.
# Sends the user to their dashboard page.
@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        # Store user form input
        username = request.form["username"]
        password = request.form["password"]

        # Login validation
        error_message = login_validation(username, password)
        if error_message:
            return render_template("login.html", error=error_message)        
        
        # Login authentication
        is_valid_user = login_authentication(username, password)
        if is_valid_user:
            # Allow user to access dashboard
            session["username"] = username  # store session variable
            return redirect(url_for("dashboard", username=session["username"]))
        else:
            # Send user back to login page
            return render_template("login.html", error="Invalid username or password")
        
    return render_template("login.html")

def login_validation(username, password):
    if username == '' and password == '':
        return "Please enter a username and password"
    elif username == '':
        return "Please enter a username"
    elif password == '':
        return "Please enter a password"
    # Return None if there is no error with input
    else:
        return None

def login_authentication(username, password):
    # Check database for the username
    user = User.query.filter_by(username=username).first()

    # Return True if username found and password is correct
    # Return False if username or password is incorrect
    if user and user.check_password(password):
        return True
    else:
        return False


""" Logout route """
# Logs the user out by removing the session variable.
# Sends the user to the homepage.
@app.route("/logout")
def logout():
    # Remove session variable if the user is logged in
    if "username" in session:
        session.pop("username")
    return redirect(url_for("home"))
    

""" Dashboard route """
# Directs user to the dashboard page if they are logged in.
@app.route("/dashboard")
def dashboard():
    username_in_session = False
    if "username" in session:
        # Store username as variable if user is logged in
        username_in_session = True
        username = session["username"]
        return render_template("dashboard.html", username=username, logged_in=username_in_session)
    
    return redirect(url_for("home"))


""" Search Movies route """
# Handles movie search requests by querying an external API.
# Returns a single random movie that matches user-selected filters from the homepage.
# If no movie is found, returns an error message.
@app.route("/movies", methods=["GET", "POST"])
def search_movies():
    # Check if user is logged in
    if "username" in session:
        if request.method == "POST":
            # Set up api request parameters
            url = "https://api.themoviedb.org/3/discover/movie"
            headers = {
                "accept": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5MWVhNjI5MWJjYjA0MjVlYTRiZWJmMTNmOTcyOTVlMiIsIm5iZiI6MTc1MzI5NDQzOS44MjA5OTk5LCJzdWIiOiI2ODgxMjY2NzZhMzgwNGMyMGUxNmFmZDAiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.5xA_CIxcW_VCkJPl-NrOyEUobnBwndzWmrhijGVc62o"
            }
            params = {
                "with_genres" : request.form["genre"],
                "with_runtime.lte" : request.form["runtime_lte"],
                "with_original_language" : request.form["original_language"],
                "primary_release_year" : request.form["release_year"]
            }

            # Query the api for a response
            response = requests.get(url, headers=headers, params=params)
            response_json = response.json()

            # Get random page from total number of pages
            total_pages = response_json['total_pages']
            if total_pages > 500:
                total_pages = 500
            if total_pages > 0:
                random_page = randint(1, total_pages)
            else:
                return render_template("movies.html", error="Could not find a movie. Please adjust your filters.")

            # Query the api for a response
            # this time asking for the random page
            params = {
                "with_genres" : request.form["genre"],
                "with_runtime.lte" : request.form["runtime_lte"],
                "with_original_language" : request.form["original_language"],
                "primary_release_year" : request.form["release_year"],
                "page" : random_page
            }
            response = requests.get(url, headers=headers, params=params)
            response_json = response.json()

            # Store movie data
            movies_data = response_json['results']

            # Get random movie from movies_data
            num_movies = len(movies_data)
            if num_movies > 0:
                random_movie_index = randint(0, num_movies-1)
                random_movie = movies_data[random_movie_index]
            else:
                return render_template("movies.html", error="Could not find a movie. Please adjust your filters.")
            
            # Get name of movie
            movie_name = random_movie['original_title']

            # Get poster of movie
            movie_id = random_movie['id']
            url = f"https://api.themoviedb.org/3/movie/{movie_id}/images"
            response = requests.get(url, headers=headers)
            response_json = response.json()
            poster = response_json.get('posters', [])
            if poster:
                poster_url = poster[0]['file_path']
            else:
                poster_url = ""

            return render_template("movies.html", title=movie_name, poster_url_path=poster_url)
        return render_template("movies.html", error="Click Find!")
    else:
        return redirect(url_for("login"))


# Search TvShows route
@app.route("/tvshows", methods=["GET", "POST"])
def search_tvshows():
    # Check if user is logged in
    if "username" in session:
        if request.method == "POST":
            # Set up api request parameters
            url = "https://api.themoviedb.org/3/discover/tv"
            headers = {
                "accept": "application/json",
                "Authorization": "Bearer eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiI5MWVhNjI5MWJjYjA0MjVlYTRiZWJmMTNmOTcyOTVlMiIsIm5iZiI6MTc1MzI5NDQzOS44MjA5OTk5LCJzdWIiOiI2ODgxMjY2NzZhMzgwNGMyMGUxNmFmZDAiLCJzY29wZXMiOlsiYXBpX3JlYWQiXSwidmVyc2lvbiI6MX0.5xA_CIxcW_VCkJPl-NrOyEUobnBwndzWmrhijGVc62o"
            }
            params = {
                "with_genres" : request.form["genre"],
                "with_runtime.lte" : request.form["runtime_lte"],
                "with_original_language" : request.form["original_language"],
                "first_air_date_year" : request.form["first_air_date_year"]
            }

            # Query the api for a response
            response = requests.get(url, headers=headers, params=params)
            response_json = response.json()
            print(f"\n\nFirst Response:\n{response_json}\n\n")

            # Get random page from all the pages
            total_pages = response_json['total_pages']
            if total_pages > 0:
                random_page = randint(1, total_pages)
            else:
                return render_template("tvshows.html", error="Could not find a tv show. Please adjust your filters.")
            
            # Query the api for a response
            # this time asking for the random page
            params = {
                "with_genres" : request.form["genre"],
                "with_runtime.lte" : request.form["runtime_lte"],
                "with_original_language" : request.form["original_language"],
                "first_air_date_year" : request.form["first_air_date_year"],
                "page" : random_page
            }
            response = requests.get(url, headers=headers, params=params)
            response_json = response.json()

            # Store tv show data
            tvshows_data = response_json['results']

            # Get random movie from tvshows_data
            num_tvshows = len(tvshows_data)
            if num_tvshows > 0:
                random_tvshow_index = randint(0, num_tvshows-1)
                random_tvshow = tvshows_data[random_tvshow_index]
            else:
                return render_template("tvshows.html", error="Could not find a tv show. Please adjust your filters.")
            
            # Get name of tv show
            tvshow_name = random_tvshow['original_name']

            # Get poster of tv show
            tvshow_id = random_tvshow['id']
            url = f"https://api.themoviedb.org/3/tv/{tvshow_id}/images"
            response = requests.get(url, headers=headers)
            response_json = response.json()
            poster = response_json.get('posters', [])
            if poster:
                poster_url = poster[0]['file_path']
            else:
                poster_url = ""

            return render_template("tvshows.html", title=tvshow_name, poster_url_path=poster_url)
        return render_template("tvshows.html", error="Click Find!")
    else:
        return redirect(url_for("login"))
    

# Search All Tv route
@app.route("/all-tv")
def search_all():
    if "username" in session:
        return render_template("all-tv.html")
    else:
        return redirect(url_for("login"))
    

# About Me route
@app.route("/aboutme")
def about_me():
    if "username" in session:
        return render_template("aboutme.html", isInSession=True)
    else:
        return render_template("aboutme.html", isInSession=False)


# Error404 route
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
