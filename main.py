import os
import requests
from dotenv import load_dotenv
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from movie import Movie
from tv_show import TVShow
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import relationship
from forms import SearchForm, RegisterForm, LoginForm, ChangePassword
from flask_login import UserMixin, login_user, LoginManager, login_required, current_user, logout_user
from werkzeug.security import generate_password_hash, check_password_hash

load_dotenv()
app = Flask(__name__)
app.config['SECRET_KEY'] = os.getenv("APP_SECRET_KEY")
Bootstrap(app)

# CONNECT TO DB
app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get("DATABASE")
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

# LOGIN MANAGER
login_manager = LoginManager()
login_manager.init_app(app)


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# DB TABLES


class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(250), unique=True)
    password = db.Column(db.String(250))
    name = db.Column(db.String(250))


class List(db.Model):
    __tablename__ = "list"
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("users.id"))
    name = db.Column(db.String(250))


class ListItem(db.Model):
    __tablename__ = "list_item"
    id = db.Column(db.Integer, primary_key=True)
    list_id = db.Column(db.Integer, db.ForeignKey("list.id"))
    content_id = db.Column(db.Integer)
    content_title = db.Column(db.String(250))
    content_poster_path = db.Column(db.String(250))
    content_type = db.Column(db.String(10))


db.create_all()

API_KEY = os.getenv("API_KEY")
TMDB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
TMDB_TV_SHOW_SEARCH_URL = "https://api.themoviedb.org/3/search/tv"
TMDB_INFO_URL = "https://api.themoviedb.org/3/movie"
TMDB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"
TMDB_TV_URL = "https://api.themoviedb.org/3/tv"


@app.route("/register", methods=["GET", "POST"])
def register():
    register_form = RegisterForm()
    if request.method == "POST":

        # CHECK IF USER ALREADY EXISTS IN DB
        if User.query.filter_by(email=register_form.email.data).first():
            flash("Email address already in use, please sign in instead.")
            return redirect(url_for('login'))

        name = register_form.name.data
        email = register_form.email.data
        password = register_form.password.data

        # HASH USERS PW
        password_hash = generate_password_hash(
            password,
            method='pbkdf2:sha256',
            salt_length=8
        )

        new_user = User(
            name=name,
            email=email,
            password=password_hash
        )

        # ADD USER TO DB
        db.session.add(new_user)
        db.session.commit()

        login_user(new_user)

        watchlist = List(
            user_id=current_user.id,
            name="Watchlist"
        )

        favourites = List(
            user_id=current_user.id,
            name="Favourites"
        )

        db.session.add(watchlist)
        db.session.add(favourites)
        db.session.commit()

        return redirect(url_for('search'))
    return render_template("sign-up.html", form=register_form, current_user=current_user)


@ app.route("/login", methods=["GET", "POST"])
def login():
    login_form = LoginForm()
    if request.method == "POST":
        email = login_form.email.data
        password = login_form.password.data

        user = User.query.filter_by(email=email).first()

        # Email doesn't exist
        if not user:
            flash("We cannot find an account with that email address. Please try again.")
            return redirect(url_for('login'))
        # Password incorrect
        elif not check_password_hash(user.password, password):
            flash('Password incorrect, please try again.')
            return redirect(url_for('login'))
        else:
            login_user(user)
            return redirect(url_for('search'))
    return render_template("login.html", form=login_form, current_user=current_user)


@ app.route("/logout")
def logout():
    logout_user()
    return redirect(url_for('search'))


@ app.route("/watchlist")
def watchlist():
    user_watchlist = List.query.filter_by(user_id=current_user.id).first(
    ) and List.query.filter_by(name="Watchlist").first()
    watchlist_items = ListItem.query.filter_by(list_id=user_watchlist.id)
    for item in watchlist_items:
        print(f"Watchlist URL: {item}")
    return render_template("watchlist.html", current_user=current_user, watchlist=user_watchlist, watchlist_items=watchlist_items)


@ app.route("/add-to-watchlist")
def add_to_watchlist():

    # GETS CURRENT USER'S WATCHLIST
    user_watchlist = List.query.filter_by(user_id=current_user.id).first(
    ) and List.query.filter_by(name="Watchlist").first()

    # CHECK IF ITEM ALREADY EXISTS IN WATCHLIST
    content_id = request.args.get("id")
    content_type = request.args.get("content_type")

    if ListItem.query.filter_by(list_id=current_user.id).first() and ListItem.query.filter_by(
            content_id=content_id).first() and ListItem.query.filter_by(content_type=content_type).first():
        flash("Item already exists in watchlist.")
        return redirect(url_for('watchlist'))

    # CREATE NEW WATCHLIST ITEM
    new_watchlist_item = ListItem(
        list_id=user_watchlist.id,
        content_id=request.args.get("id"),
        content_title=request.args.get("title"),
        content_poster_path=request.args.get("poster_path"),
        content_type=request.args.get("content_type")
    )

    db.session.add(new_watchlist_item)
    db.session.commit()

    watchlist_items = ListItem.query.filter_by(list_id=user_watchlist.id).all()

    return render_template("watchlist.html", current_user=current_user, watchlist=user_watchlist, watchlist_items=watchlist_items)


@ app.route("/remove-from-watchlist")
def remove_from_watchlist():

    content_id = request.args.get("id")
    content_to_delete = ListItem.query.filter_by(content_id=content_id).first()

    db.session.delete(content_to_delete)
    db.session.commit()

    return redirect(url_for('watchlist'))


@app.route("/favourites")
def favourites():

    user_favourites = List.query.filter_by(user_id=current_user.id).first(
    ) and List.query.filter_by(name="Favourites").first()

    favourites_items = ListItem.query.filter_by(
        list_id=user_favourites.id).all()

    return render_template("favourites.html", current_user=current_user, favourites=user_favourites, favourites_items=favourites_items)


@app.route("/add-to-favourites")
def add_to_favourites():

    # GETS CURRENT USER'S FAVOURITE LIST
    user_favourites = List.query.filter_by(user_id=current_user.id).first(
    ) and List.query.filter_by(name="Favourites").first()
    print(user_favourites.id)

    # CHECK IF ITEM ALREADY EXISTS IN FAVOURITES
    content_id = request.args.get("id")
    content_type = request.args.get("content_type")

    if ListItem.query.filter_by(list_id=current_user.id).first() and ListItem.query.filter_by(
            content_id=content_id).first() and ListItem.query.filter_by(content_type=content_type).first():
        flash("Item already exists in favourites.")
        return redirect(url_for('favourites'))

    # CREATE NEW FAVOURITES ITEM
    new_favourites_item = ListItem(
        list_id=user_favourites.id,
        content_id=request.args.get("id"),
        content_title=request.args.get("title"),
        content_poster_path=request.args.get("poster_path"),
        content_type=request.args.get("content_type")
    )

    db.session.add(new_favourites_item)
    db.session.commit()

    favourites_items = ListItem.query.filter_by(
        list_id=user_favourites.id).all()

    return render_template("favourites.html", current_user=current_user, favourites=user_favourites, favourites_items=favourites_items)


@app.route("/remove-from-favourites")
def remove_from_favourites():
    content_id = request.args.get("id")
    content_to_delete = ListItem.query.filter_by(content_id=content_id).first()

    db.session.delete(content_to_delete)
    db.session.commit()

    return redirect(url_for('favourites'))


@ app.route("/edit-profile")
def edit_profile():
    return render_template("edit-profile.html", current_user=current_user)


@ app.route("/change-password", methods=["GET", "POST"])
def change_password():

    change_pw_form = ChangePassword()

    if request.method == "POST":
        if not check_password_hash(current_user.password, change_pw_form.current_password.data):
            flash("Current password does not match. Please try again.")
            return redirect(url_for('change_password'))
        elif not change_pw_form.new_password.data == change_pw_form.confirm_new_password.data:
            flash("Passwords do not match. Please try again.")
            return redirect(url_for('change_password'))
        else:
            flash("Password changed successfully.")
            return redirect(url_for('edit_profile'))
            new_password = change_pw_form.new_password.data
            current_user.password = generate_password_hash(
                new_password,
                method='pbkdf2:sha256',
                salt_length=8
            )
            db.session.commit()

    return render_template("change-password.html", current_user=current_user, form=change_pw_form)


@app.route("/search", methods=["GET", "POST"])
def search():
    search_form = SearchForm()
    if request.method == "POST":
        title = search_form.title.data
        print(title)
        params = {
            "api_key": API_KEY,
            "query": title,
            "language": "en-US",
            "page": "1"
        }

        movie_response = requests.get(url=TMDB_SEARCH_URL, params=params)
        tv_show_response = requests.get(
            url=TMDB_TV_SHOW_SEARCH_URL, params=params)

        movie_data = movie_response.json()["results"]
        tv_show_data = tv_show_response.json()["results"]

        return render_template("select.html", movie_options=movie_data, tv_show_options=tv_show_data)
    return render_template("search.html", form=search_form)


@app.route("/", methods=["GET", "POST"])
def search_movie():
    search_form = SearchForm()
    if search_form.validate_on_submit():
        title = search_form.title.data
        params = {
            "api_key": API_KEY,
            "query": title,
            "language": "en-US",
            "page": "1"
        }

        response = requests.get(url=TMDB_SEARCH_URL, params=params)
        movie_data = response.json()["results"]
        return render_template("select.html", options=movie_data)
    return render_template("index.html", form=search_form)


@app.route("/movie/", methods=["GET", "POST"])
def movie():
    page_number = request.args.get("page_number")
    movie_type = request.args.get("movie_type")
    url = f"{TMDB_INFO_URL}/{movie_type}"
    response = requests.get(url=url,
                            params={
                                "api_key": API_KEY,
                                "page": page_number
                            })
    movie_data = response.json()["results"]

    return render_template("media-results.html", movie_type=movie_type, movies=movie_data, is_movie=True)


@app.route("/find")
def find_movie():
    movie_id = request.args.get("id")
    if movie_id:
        movie_api_url = f"{TMDB_INFO_URL}/{movie_id}"
        response = requests.get(url=movie_api_url, params={"api_key": API_KEY})
        data = response.json()

        similar_movies_url = f"{TMDB_INFO_URL}/{movie_id}/similar"
        similar_movies_response = requests.get(
            url=similar_movies_url, params={"api_key": API_KEY})
        similar_movies_data = similar_movies_response.json()["results"]

        credit_response = requests.get(
            url=f"{movie_api_url}/credits", params={"api_key": API_KEY})
        credit_data = credit_response.json()

        for crew in credit_data["crew"]:
            if crew["job"] == "Director":
                director = (crew["name"])

        cast = [cast["name"] for cast in credit_data["cast"][:10]]
        genres = [genre["name"] for genre in data["genres"]]
        user_score = int(data["vote_average"] * 10)

        movie = Movie(
            id=data["id"],
            title=data["title"],
            content_type='movie',
            director=director,
            cast=", ".join(cast),
            genre=", ".join(genres),
            overview=data["overview"],
            release_date=data["release_date"],
            tagline=data["tagline"],
            runtime=data["runtime"],
            user_score=user_score,
            poster_url=f"{TMDB_IMAGE_URL}/{data['poster_path']}"
        )
        return render_template("content-info.html", movie=movie, similar_movies=similar_movies_data, img_url=TMDB_IMAGE_URL, is_movie=True)


@app.route("/find-tv-shows")
def find_tv_show():
    tv_show_id = request.args.get("id")
    if tv_show_id:
        tv_show_url = f"{TMDB_TV_URL}/{tv_show_id}"
        response = requests.get(url=tv_show_url, params={"api_key": API_KEY})
        data = response.json()

        similar_tv_shows_url = f"{TMDB_TV_URL}/{tv_show_id}/similar"
        similar_tv_shows_response = requests.get(
            url=similar_tv_shows_url, params={"api_key": API_KEY})
        similar_tv_shows_data = similar_tv_shows_response.json()[
            "results"]

        credit_response = requests.get(
            url=f"{tv_show_url}/credits", params={"api_key": API_KEY})
        credit_data = credit_response.json()

        cast = [cast["name"] for cast in credit_data["cast"][:10]]
        genres = [genre["name"] for genre in data["genres"]]
        user_score = int(data["vote_average"] * 10)

        try:
            creator = data["created_by"][0]["name"]
        except IndexError:
            creator = None

        tv_show = TVShow(
            id=data["id"],
            title=data["name"],
            content_type='tv',
            creator=creator,
            cast=", ".join(cast),
            genre=", ".join(genres),
            overview=data["overview"],
            first_air_date=data["first_air_date"],
            episode_run_time=data["episode_run_time"][0],
            number_of_seasons=data["number_of_seasons"],
            tagline=data["tagline"],
            user_score=user_score,
            poster_url=f"{TMDB_IMAGE_URL}/{data['poster_path']}"
        )

        return render_template("content-info.html", tv_show=tv_show, similar_tv_shows=similar_tv_shows_data, img_url=TMDB_IMAGE_URL, is_tv_show=True)


@app.route("/tv-show", methods=["GET", "POST"])
def tv_show():
    page_number = request.args.get("page_number")
    tv_show_type = request.args.get("tv_show_type")
    url = f"{TMDB_TV_URL}/{tv_show_type}"
    response = requests.get(url=url,
                            params={
                                "api_key": API_KEY,
                                "page": page_number
                            })
    tv_show_data = response.json()["results"]
    return render_template("media-results.html", tv_show_type=tv_show_type, tv_shows=tv_show_data, is_tv_show=True)


if __name__ == "__main__":
    app.run(debug=True)
