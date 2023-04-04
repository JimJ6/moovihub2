from flask import Flask, render_template, url_for, request, redirect, flash, session
import requests
from flask_mysqldb import MySQL
from flask_bcrypt import Bcrypt
import math
import os
import random
import re
import json
from collections import Counter, OrderedDict
from datetime import datetime, timedelta

app = Flask(__name__)
bcrypt = Bcrypt(app)


app.config['SECRET_KEY'] = os.urandom(24)
api_key = '59fedc35f4684e7855ce030b158c950d'


# DB


app.config['MYSQL_HOST'] = os.environ.get('MYSQL_HOST')
app.config['MYSQL_USER'] = os.environ.get('MYSQL_USER')
app.config['MYSQL_PASSWORD'] = os.environ.get('MYSQL_PASSWORD')
app.config['MYSQL_DB'] = os.environ.get('MYSQL_DB')
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
mysql = MySQL(app)


# Function to generate current date in SQL format(YYYY-MM-DD)


def get_current_date():
    now = datetime.now()
    return now.strftime('%Y-%m-%d')

# Function to generate current date/time in SQL format(YYYY-MM-DD)


def get_current_datetime():
    now = datetime.now()
    return now.strftime('%Y-%m-%d %H:%M:%S')


@app.route('/', methods=['GET', 'POST'])
def index():

    if 'USER_ID' in session:

        return redirect(url_for('home'))

    if request.form:

        form = request.form

        if 'password confirm' in request.form:

            session['FORM_NAME'] = "signup"
            # USERNAME VALIDATION
            if form['username'] == "" or form['password'] == "" or form['password confirm'] == "":

                flash('Please enter details for all fields!', 'error')
                return redirect(request.url)

            elif len(form['username']) < 5 or len(form['username']) > 15:

                flash('Username must be between 5 and 15 characters!', 'error')
                return redirect(request.url)

            cursor = mysql.connection.cursor()
            cursor.execute(
                'SELECT * FROM user_info WHERE username = %s', (form['username'],))
            user_exists = cursor.fetchone()
            if user_exists:
                flash('Sorry, that username is already taken!', 'error')
                return redirect(request.url)

            # PASSWORD VALIDATION
            if len(form['password']) < 6 or len(form['password']) > 12:

                flash('Your password should contain 6 - 12 characters!', 'error')
                return redirect(request.url)

            # uses regular expression to check if an uppercase letter exists
            elif not re.search('[A-Z]', form['password']):

                flash(
                    'Your password should contain at least one uppercase letter!', 'error')
                return redirect(request.url)

            # uses regular expression to check if a number exists
            elif not re.search('[0-9]', form['password']):

                flash('Your password should contain at least one number!', 'error')
                return redirect(request.url)

            # checks if password and confirm_password fields are not equal
            elif form['password'] != form['password confirm']:

                flash('Passwords do not match!', 'error')
                return redirect(request.url)

            # IF FORM PASSES ALL VALIDATION STEPS

            password_hash = bcrypt.generate_password_hash(
                form['password']).decode('utf-8')
            username = form['username']
            current_date = get_current_date()

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO user_info(username, password, date_joined) VALUES(%s, %s, %s)",
                        (username, password_hash, current_date))
            mysql.connection.commit()
            cur.close()

            cursor = mysql.connection.cursor()
            cursor.execute(
                "SELECT user_id, username FROM user_info WHERE username = %s", (form['username'],))
            session_user = cursor.fetchone()
            cursor.close()

            session['USER_ID'] = session_user['user_id']
            session['USERNAME'] = session_user['username']
            session.pop('FORM_NAME', None)

            flash(
                f'Welcome {session["USERNAME"]}, you have successfully registered!', 'success')
            return redirect(url_for('home'))

        else:

            session['FORM_NAME'] = "login"

            if form['username'] == "" or form['password'] == "":

                flash('Please enter details for all fields!', 'error')
                return redirect(request.url)

            cursor = mysql.connection.cursor()
            cursor.execute(
                'SELECT * FROM user_info WHERE username = %s', (form['username'],))
            user = cursor.fetchone()
            cursor.close()

            if user:

                if bcrypt.check_password_hash(user['password'], form['password']):

                    cursor = mysql.connection.cursor()
                    cursor.execute(
                        "SELECT user_id, username FROM user_info WHERE username = %s", (form['username'],))
                    session_user = cursor.fetchone()
                    cursor.close()

                    session['USER_ID'] = session_user['user_id']
                    session['USERNAME'] = session_user['username']

                    flash(
                        f'Welcome {session["USERNAME"]}, you have successfully logged in!', 'success')
                    return redirect(url_for('home'))

                else:

                    flash('Incorrect Password', 'error')
                    return redirect(request.url)

            else:

                flash('Username does not exist', 'error')
                return redirect(request.url)

    return render_template('index.html')


@app.route('/home/new-releases')
def home():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    # List variable to store movies
    new_releases = []

    # Get the first 200 new release films (first 10 page results * 20 movies per page = 200)
    # i = 1 since we're starting on page 1
    i = 1
    while i <= 10:

        url = "https://api.themoviedb.org/3/movie/now_playing?api_key=" + \
            api_key + "&language=en-US&page=" + str(i)
        req = requests.get(url, verify=False)
        # add the results from current page index to the list
        # results is the json object key that stores the movie results so that's what we add
        new_releases.extend(json.loads(req.text)['results'])
        i = i + 1

    return render_template('home.html', new_releases=new_releases)


@app.route('/home/popular')
def home_popular():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    # List variable to store movies
    popular_movies = []

    # Get the first 200 popular films (first 10 page results * 20 movies per page = 200)
    # i = 1 since we're starting on page 1
    i = 1
    while i <= 10:

        url = "https://api.themoviedb.org/3/movie/popular?api_key=" + \
            api_key + "&language=en-US&page=" + str(i)
        req = requests.get(url, verify=False)
        # add the results from current page index to the list
        # results is the json object key that stores the movie results so that's what we add
        popular_movies.extend(json.loads(req.text)['results'])
        i = i + 1

    return render_template('home_popular.html', popular_movies=popular_movies)


@app.route('/home/highest-rated')
def home_highest_rated():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    # List variable to store movies
    highest_rated_movies = []

    # Get the first 200 highest rated films (first 10 page results * 20 movies per page = 200)
    # i = 1 since we're starting on page 1
    i = 1
    while i <= 10:

        url = "https://api.themoviedb.org/3/movie/top_rated?api_key=" + \
            api_key + "&language=en-US&page=" + str(i)
        req = requests.get(url, verify=False)
        # add the results from current page index to the list
        # results is the json object key that stores the movie results so that's what we add
        highest_rated_movies.extend(json.loads(req.text)['results'])
        i = i + 1

    return render_template('home_highest_rated.html', highest_rated_movies=highest_rated_movies)


@app.route('/search', methods=['GET', 'POST'])
def search():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    if request.method == "POST":

        if request.form['search'] == "":

            error_message = True

            return render_template('search.html', error_message=error_message)

        query = request.form['search']

        search_url = "https://api.themoviedb.org/3/search/movie?api_key=" + \
            api_key + "&language=en-US&query=" + query + "&page=1&include_adult=false"
        search_request = requests.get(search_url, verify=False)
        results = json.loads(search_request.text)

        total_pages = results['total_pages']
        movies = []

        i = 1
        while i <= total_pages:

            url = "https://api.themoviedb.org/3/search/movie?api_key=" + api_key + \
                "&language=en-US&query=" + query + \
                "&page=" + str(i) + "&include_adult=false"
            req = requests.get(url, verify=False)
            movies.extend(json.loads(req.text)['results'])
            i = i + 1

        total_movies = 0
        for movie in movies:

            if movie['poster_path']:
                total_movies += 1

        if total_movies == 0:
            no_results = True
            return render_template('search.html', movies=movies, total_movies=total_movies, query=query, no_results=no_results)

        return render_template('search.html', movies=movies, total_movies=total_movies, query=query)

    return render_template('search.html')


@app.route('/advanced-search', methods=['GET', 'POST'])
def advanced_search():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':

        form = request.form

        if 'genre' not in form:

            flash('Please include at least one genre in your search!', 'info')
            return redirect(request.url)

        sort_by = form['sort']
        year = form['year']
        genres = ",".join(form.getlist('genre'))
        genres_checked = form.getlist('genre')

        search_url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + "&language=en-US&sort_by=" + sort_by + \
            "&include_adult=false&include_video=false&page=1&primary_release_year=" + \
            str(year) + "&with_genres=" + genres
        search_request = requests.get(search_url, verify=False)
        results = json.loads(search_request.text)

        total_pages = results['total_pages']
        movie_results = []

        i = 1
        while i <= total_pages:

            url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + "&language=en-US&sort_by=" + sort_by + \
                "&include_adult=false&include_video=false&page=" + \
                str(i) + "&primary_release_year=" + \
                str(year) + "&with_genres=" + genres
            req = requests.get(url, verify=False)
            movie_results.extend(json.loads(req.text)['results'])
            i += 1

        results_total = 0
        for movie in movie_results:

            if movie['poster_path']:
                results_total += 1

        if results_total == 0:
            no_results = True
            return render_template('advanced_search.html',
                                   no_results=no_results,
                                   sort_by=sort_by,
                                   year=year,
                                   genres_checked=genres_checked)

        else:

            return render_template('advanced_search.html', movie_results=movie_results,
                                   results_total=results_total,
                                   sort_by=sort_by,
                                   year=year,
                                   genres_checked=genres_checked)

    sort_by = "popularity.desc"
    year = "2021"
    genres_checked = []

    return render_template('advanced_search.html',
                           sort_by=sort_by,
                           year=year,
                           genres_checked=genres_checked)


@app.route('/my-stats')
def my_stats():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    # USER STATS ARE BASED OFF THEIR WATCHED MOVIES

    # ---------- GET USERS TOTAL MOVIE COUNT ----------
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT COUNT(movie_id) AS total_movies FROM user_watched WHERE user_id = %s', (session['USER_ID'],))
    total_movies = cursor.fetchone()['total_movies']

    # ---------- GET USERS TOTAL WATCHED TIME ----------
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT SUM(runtime) AS total_runtime FROM user_watched WHERE user_id = %s', (session['USER_ID'],))
    total_runtime = cursor.fetchone()['total_runtime']

    if total_runtime:

        # runtime is in minutes so we convert to days, hours and minutes
        total_minutes = total_runtime

        # step 1 - get total days (1440 minutes in a day)
        days = math.floor(total_minutes / 1440)
        remaining_minutes = total_minutes % 1440

        # step 2 - get total hours
        hours = math.floor(remaining_minutes / 60)

        # step 3 - get total minutes left over
        minutes = remaining_minutes % 60

    else:

        days = 0
        hours = 0
        minutes = 0

    # ---------- GET USERS TOTAL RATINGS ----------

    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT COUNT(movie_id) AS total_ratings FROM user_rated WHERE user_id = %s', (session['USER_ID'],))
    total_ratings = cursor.fetchone()['total_ratings']
    cursor.close()

    # ---------- GET USERS AVERAGE RATING ----------

    # step 1 - get all user rating score from database table
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT rating_score FROM user_rated WHERE user_id = %s', (session['USER_ID'],))
    rating_scores = cursor.fetchall()
    cursor.close()

    if len(rating_scores) > 0:

        # step 2 - store rating scores in a list by looping through cursor results
        scores = []

        for record in rating_scores:

            scores.append(record['rating_score'])

        # step 3 - divide the sum of the ratings by the number of ratings and round the floating value
        average_score = round(sum(scores)/len(scores))

        # step 4 - result will be a integer with decimal of zero so we isolate the integer part using split string method
        average_rating = int(str(average_score).split('.')[0])

    else:

        average_rating = 0

    # ---------- GET USERS TOP ACTORS BY MOVIE COUNT ----------

    # step 1 - get all actors from each users movie in database
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT cast FROM user_watched WHERE user_id = %s', (session['USER_ID'],))
    movie_casts = cursor.fetchall()
    cursor.close()

    actor_occurences = []

    for movie in movie_casts:

        cast = movie['cast']
        actor_occurences.extend(cast.split(','))

    top_5_actors = Counter(actor_occurences).most_common(5)

    actors_labels = []
    actors_data = []

    for actor, movie_count in top_5_actors:

        actors_labels.append(actor)
        actors_data.append(movie_count)

    # ---------- GET USERS TOP DIRECTORS BY MOVIE COUNT ----------

    # step 1 - get all directors from each users movie in database
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT directors FROM user_watched WHERE user_id = %s', (session['USER_ID'],))
    movie_directors = cursor.fetchall()
    cursor.close()

    director_occurences = []

    for movie in movie_directors:

        directors = movie['directors']
        director_occurences.extend(directors.split(','))

    top_5_directors = Counter(director_occurences).most_common(5)

    directors_labels = []
    directors_data = []

    for director, movie_count in top_5_directors:

        directors_labels.append(director)
        directors_data.append(movie_count)

    # ---------- GET USERS TOP GENRES BY MOVIE COUNT ----------

    # step 1 - get all genres from each users movie in database
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT genres FROM user_watched WHERE user_id = %s', (session['USER_ID'],))
    movie_genres = cursor.fetchall()
    cursor.close()

    genre_occurences = []

    for movie in movie_genres:

        genres = movie['genres']
        genre_occurences.extend(genres.split(','))

    top_5_genres = Counter(genre_occurences).most_common(5)

    genres_labels = []
    genres_data = []

    for genre, movie_count in top_5_genres:

        genres_labels.append(genre)
        genres_data.append(movie_count)

    # ---------- GET USERS TOP 5 YEARS BY MOVIE COUNT ----------

    # step 1 - get all release dates from users movie from watched database table
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT release_date FROM user_watched WHERE user_id = %s', (session['USER_ID'],))
    movie_release_dates = cursor.fetchall()
    cursor.close()

    year_occurences = []

    for movie in movie_release_dates:

        year = movie['release_date'][:4]
        year_occurences.append(year)

    top_5_years = Counter(year_occurences).most_common(5)

    years_labels = []
    years_data = []

    for year, movie_count in top_5_years:

        years_labels.append(year)
        years_data.append(movie_count)

    print(years_labels)
    print(years_data)

    # ---------- GET DECADE DISTRIBUTION OF USERS TOTAL WATCHED MOVIES ----------

    # step 1 - create dictionary to hold decades and movie count from 1930 - 2020
    # use OrderDict container from collections module
    decades = OrderedDict()
    decades['1930s'] = 0
    decades['1940s'] = 0
    decades['1950s'] = 0
    decades['1960s'] = 0
    decades['1970s'] = 0
    decades['1980s'] = 0
    decades['1990s'] = 0
    decades['2000s'] = 0
    decades['2010s'] = 0
    decades['2020s'] = 0

    # step 2 - get all release dates from users movie from watched database table
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT release_date FROM user_watched WHERE user_id = %s', (session['USER_ID'],))
    movie_release_dates = cursor.fetchall()
    cursor.close()

    # step 3 - get decade of each movie and add 1 to the value of respective decade key in decades dictionary
    for movie in movie_release_dates:

        # release_date is an int type (YYYY-MM-DD) so we convert to string, slice it and concatenate to get the decade
        decade = str(movie['release_date'][:3]) + "0s"
        decades[decade] += 1

    # step 4 - loop through the decades and add decade and movie count to separate lists for data chart

    decades_labels = []
    decades_data = []
    for key, value in decades.items():

        decades_labels.append(key)
        decades_data.append(value)

    # ---------- GET RATING ASPECTS OF USERS TOTAL RATED MOVIES ----------

    # step 1 - create dictionary to hold the aspects and their respective rating count
    # use OrderDict container from collections module
    rated_aspects = OrderedDict()
    rated_aspects['acting'] = 0
    rated_aspects['directing'] = 0
    rated_aspects['theme'] = 0
    rated_aspects['genre'] = 0
    rated_aspects['cinematography'] = 0
    rated_aspects['writing'] = 0
    rated_aspects['sound'] = 0

    # step 2 - get all liked aspects from users movie ratings
    cursor = mysql.connection.cursor()
    cursor.execute(
        'SELECT liked FROM user_rated WHERE user_id = %s', (session['USER_ID'],))
    movie_liked = cursor.fetchall()
    cursor.close()

    aspect_occurences = []
    # step 3 - get decade of each movie and add 1 to the value of respective decade key in decades dictionary
    for movie in movie_liked:

        # if liked column is not null
        if movie['liked']:

            # split the string into a list and extend like_occurences list with the new list
            aspect_occurences.extend(movie['liked'].split(','))

    # step 4 - iterate through the occurences of the aspects and add value of 1 to the respective dictionary key

    for aspect in aspect_occurences:

        rated_aspects[aspect] += 1

    # step 5 - loop through the rated_aspects dictionary and add aspect and rating count to separate lists for data chart

    rating_aspects_labels = []
    rating_aspects_data = []
    for key, value in rated_aspects.items():

        rating_aspects_labels.append(key.capitalize())
        rating_aspects_data.append(value)

    # USED TO DISPLAY ASSIOCATED TEXT WITH RATING ICON IN AVERAGE RATING STAT TILE
    rating_descriptions = {
        "1": "Hated it",
        "2": "Not for Me",
        "3": "Watchable",
        "4": "Liked it!",
        "5": "Loved it!",
    }

    return render_template('my_stats.html',
                           total_movies=total_movies,
                           days=days,
                           hours=hours,
                           minutes=minutes,
                           total_ratings=total_ratings,
                           average_rating=average_rating,
                           rating_descriptions=rating_descriptions,
                           actors_labels=actors_labels,
                           actors_data=actors_data,
                           directors_labels=directors_labels,
                           directors_data=directors_data,
                           genres_labels=genres_labels,
                           genres_data=genres_data,
                           years_labels=years_labels,
                           years_data=years_data,
                           decades_labels=decades_labels,
                           decades_data=decades_data,
                           rating_aspects_labels=rating_aspects_labels,
                           rating_aspects_data=rating_aspects_data,
                           )


@app.route('/movie/<int:movie_id>', methods=['GET', 'POST'])
def movie_info(movie_id):

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    if request.method == 'POST':

        # IF THE USER CLICKED THE WATCHED ICON
        if 'watched' in request.form:

            movie_id = request.form['movie_id']
            user_id = session['USER_ID']
            movie_title = request.form['movie_title']
            poster_path = request.form['poster_path']
            directors = request.form['movie_directors']
            genres = request.form['movie_genres']
            cast = request.form['movie_cast']
            runtime = request.form['movie_runtime']
            release_date = request.form['movie_release_date']
            date_added = get_current_datetime()

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO user_watched(user_id, movie_id, movie_title, poster_path, genres, directors, cast, release_date, runtime, date_added) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                        (user_id, movie_id, movie_title, poster_path, genres, directors, cast, release_date, runtime, date_added))
            mysql.connection.commit()
            cur.close()

            flash('Movie successfully added to your watched movies!', 'success')
            return redirect(request.url)

        # IF THE USER CLICKED THE SAVE ICON
        if 'save' in request.form:

            movie_id = request.form['movie_id']
            user_id = session['USER_ID']
            movie_title = request.form['movie_title']
            poster_path = request.form['poster_path']
            date_added = get_current_datetime()

            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO user_saved(user_id, movie_id, movie_title, poster_path, date_added) VALUES(%s, %s, %s, %s, %s)",
                        (user_id, movie_id, movie_title, poster_path, date_added))
            mysql.connection.commit()
            cur.close()

            flash('Movie successfully added to your saved movies!', 'success')
            return redirect(request.url)

        # IF USER CLICK ON RATE ICON
        if 'rate' in request.form:

            if 'score' not in request.form:

                flash(
                    'Rating not submitted. Please include an overall rating score!', 'error')
                return redirect(request.url)

            movie_id = request.form['movie_id']
            user_id = session['USER_ID']
            movie_title = request.form['movie_title']
            poster_path = request.form['poster_path']
            directors = request.form['movie_directors']
            genres = request.form['movie_genres']
            cast = request.form['movie_cast']
            runtime = request.form['movie_runtime']
            release_date = request.form['movie_release_date']
            date_added = get_current_datetime()
            rating_score = request.form['score']

            if 'liked' in request.form:

                liked = ",".join(request.form.getlist('liked'))

            else:
                liked = None

            # INSERT RATING INTO RATING TABLE
            cur = mysql.connection.cursor()
            cur.execute("INSERT INTO user_rated(user_id, movie_id, movie_title, poster_path, rating_score, liked, date_added) VALUES(%s, %s, %s, %s, %s, %s, %s)",
                        (user_id, movie_id, movie_title, poster_path, rating_score, liked, date_added))
            mysql.connection.commit()
            cur.close()

            # MYSQL CURSOR TO FETCH ALL USER'S WATCHED MOVIES
            cur = mysql.connection.cursor()
            check_watched_results = cur.execute(
                "SELECT movie_id FROM user_watched WHERE user_id = %s", (session['USER_ID'],))

            if check_watched_results > 0:

                check_watched_results = cur.fetchall()
                check_watched_movies = []

                for movie in check_watched_results:

                    check_watched_movies.append(movie['movie_id'])

            else:
                check_watched_movies = None

            cur.close()

            # IF MOVIE NOT ALREADY IN USER'S WATCHED MOVIES, ADD IT
            # WE CAN ASSUME IF THEY ARE RATING IT, THEY HAVE WATCHED IT
            if check_watched_movies:
                if int(movie_id) not in check_watched_movies:

                    cur = mysql.connection.cursor()
                    cur.execute("INSERT INTO user_watched(user_id, movie_id, movie_title, poster_path, genres, directors, cast, release_date, runtime, date_added) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)", (
                        user_id, movie_id, movie_title, poster_path, genres, directors, cast, release_date, runtime, date_added))
                    mysql.connection.commit()
                    cur.close()

            else:
                cur = mysql.connection.cursor()
                cur.execute("INSERT INTO user_watched(user_id, movie_id, movie_title, poster_path, genres, directors, cast, release_date, runtime, date_added) VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s, %s)",
                            (user_id, movie_id, movie_title, poster_path, genres, directors, cast, release_date, runtime, date_added))
                mysql.connection.commit()
                cur.close()

            flash('Movie rating successfully added!', 'success')
            return redirect(request.url)

    # IF USER CLICK ON 'EDITING-RATING'

        if 'edit-rating' in request.form:

            if 'score' not in request.form:

                flash('Please include an overall rating score!', 'error')
                return redirect(request.url)

            user_id = session['USER_ID']
            movie_id = request.form['movie_id']
            rating_score = request.form['score']

            if 'liked' in request.form:

                liked = ",".join(request.form.getlist('liked'))

            else:
                liked = None

            date_added = get_current_datetime()

            # UPDATE RATING IN RATING TABLE
            cur = mysql.connection.cursor()
            cur.execute("UPDATE user_rated SET rating_score = %s, liked = %s WHERE user_id = %s AND movie_id = %s",
                        (rating_score, liked, session['USER_ID'], movie_id))
            mysql.connection.commit()
            cur.close()

            flash('Movie rating successfully updated!', 'success')
            return redirect(request.url)

    # MYSQL CURSOR TO FETCH ALL USER'S WATCHED MOVIES
    cur = mysql.connection.cursor()
    watched_results = cur.execute(
        "SELECT movie_id FROM user_watched WHERE user_id = %s", (session['USER_ID'],))
    if watched_results > 0:

        watched_results = cur.fetchall()
        watched_movies = []

        for movie in watched_results:

            watched_movies.append(movie['movie_id'])

    else:
        watched_movies = []

    cur.close()

    # MYSQL CURSOR TO FETCH ALL USER'S SAVED MOVIES
    cur = mysql.connection.cursor()
    saved_results = cur.execute(
        "SELECT movie_id FROM user_saved WHERE user_id = %s", (session['USER_ID'],))
    if saved_results > 0:

        saved_results = cur.fetchall()
        saved_movies = []

        for movie in saved_results:

            saved_movies.append(movie['movie_id'])

    else:
        saved_movies = None

    cur.close()

    # MYSQL CURSOR TO FETCH ALL USER'S RATED MOVIES
    cur = mysql.connection.cursor()
    rated_results = cur.execute(
        "SELECT movie_id FROM user_rated WHERE user_id = %s", (session['USER_ID'],))
    if rated_results > 0:

        rated_results = cur.fetchall()
        rated_movies = []

        for movie in rated_results:

            rated_movies.append(movie['movie_id'])

    else:

        rated_movies = None

    cur.close()

    # GET MOVIE DETAILS REQUEST GETS BASIC INFORMATION ABOUT THE CURRENT MOVIE
    details_url = 'https://api.themoviedb.org/3/movie/' + \
        str(movie_id) + '?api_key=' + api_key + '&language=en-US'
    details_request = requests.get(details_url, verify=False)
    movie_details = json.loads(details_request.text)

    # CUSTOM CODE TO GENERATE FORMATTED STRING OF RUNTIME PROPERTY FROM MINUTES TO HOURS/MINUTES

    if movie_details['runtime']:

        runtime = movie_details['runtime']
        runtime_formatted = str(timedelta(minutes=runtime))[
            0] + "h" + " " + str(timedelta(minutes=runtime))[2:4] + "min"

    else:
        runtime_formatted = None

    # CONVERT AVERAGE RATING TO SCORE OUT OF 5
    # GET VOTE AVERAGE AND CONVERT TO STRING
    vote_average = str(movie_details['vote_average'])

    # ISOLATE THE DECIMAL VALUE USING SPLIT METHOD
    round_decimal = int(vote_average.split('.')[1])

    # IF THE DECIMAL VALUE IS 5 OR GREATER, ROUND UP
    if round_decimal >= 5:
        average_rating = math.ceil(movie_details['vote_average'])
    # IF NOT, ROUND DOWN
    else:
        average_rating = math.floor(movie_details['vote_average'])

    # DIVIDING BY 2 TO GET THE VALUE OUT OF 5 RATHER THAN 10 WILL RESULT IN A FLOAT SO WE HAVE TO ROUND AGAIN
    round_decimal_2 = int(str(average_rating / 2).split('.')[1])

    if round_decimal_2 >= 5:
        average_rating = math.ceil(average_rating / 2)

    else:
        average_rating = math.floor(average_rating / 2)

    # IF CURRENT MOVIE IN USER RATINGS, GET THEIR RATING SCORE
    if rated_movies:

        if movie_details['id'] in rated_movies:
            cur = mysql.connection.cursor()
            cur.execute("SELECT rating_score FROM user_rated WHERE user_id = %s AND movie_id = %s",
                        (session['USER_ID'], movie_details['id']))
            user_rating = cur.fetchone()['rating_score']
            cur.close()

        else:
            user_rating = None

    else:
        user_rating = None

    # GET MOVIE CREDITS REQUEST
    credits_url = 'https://api.themoviedb.org/3/movie/' + \
        str(movie_id) + '/credits?api_key=' + api_key + '&language=en-US'
    credits_request = requests.get(credits_url, verify=False)
    movie_credits = json.loads(credits_request.text)

    # FOR CASES WHEN A MOVIE HAS MORE THAN ONE DIRECTOR
    # STORE DIRECTORS IN A LIST
    directors = []

    # USE FOR LOOP TO ITERATE THROUGH THE CREW OBJECT
    for member in movie_credits['crew']:
        # ADD EACH DIRECTOR TO THE LIST
        if member['job'] == 'Director':
            directors.append(member['name'])

    # CONVERT DIRECTOR LIST TO STRING FOR HTML
    directed_by = ', '.join(directors)

    # GET ONLY THE FIRST 15 ACTORS IN MOVIE CAST WHERE CAST IS GREATER THAN 15
    movie_info_cast = movie_credits['cast']

    if len(movie_info_cast) > 15:

        movie_info_cast = movie_info_cast[:15]

    else:

        movie_info_cast = movie_info_cast

    # FIND OUT IF CURRENT MOVIE BELONGS TO A COLLECTION AND IF SO, SAVE A LIST OF MOVIE'S IN THAT COLLECTION
    if movie_details['belongs_to_collection']:

        collection_id = movie_details['belongs_to_collection']['id']
        collection_url = "https://api.themoviedb.org/3/collection/" + \
            str(collection_id) + "?api_key=" + api_key + "&language=en-US"
        collection_request = requests.get(collection_url, verify=False)
        # WITHIN THE COLLECTION REQUEST, THE PARTS KEY IS THE ARRAY OF MOVIE OBJECTS WITHIN THE COLLECTION
        movie_collection = json.loads(collection_request.text)['parts']
        collection_title = json.loads(collection_request.text)['name']

    else:
        movie_collection = None
        collection_title = None

    # GET UP TO 12 MOST RECOMMENDED MOVIES FOR CURRENT MOVIE ID
    recommendations_url = "https://api.themoviedb.org/3/movie/" + \
        str(movie_id) + "/recommendations?api_key=" + \
        api_key + "&language=en-US&page=1"
    recommendations_request = requests.get(recommendations_url, verify=False)
    recommendations_results = json.loads(recommendations_request.text)
    movie_recommendations = recommendations_results['results']

    if len(movie_recommendations) > 12:

        movie_recommendations = movie_recommendations[:12]

    else:

        movie_recommendations = movie_recommendations

    # USED TO DISPLAY ASSIOCATED TEXT WITH RATING ICON IN MOVIE INFO SECTION AND RATING POP UP FORMS
    rating_descriptions = {
        "1": "Hated it",
        "2": "Not for Me",
        "3": "Watchable",
        "4": "Liked it!",
        "5": "Loved it!",
    }

    # WATCHED FORM HIDDEN INPUT VALUES FOR STORING IN WATCHED TABLE

    # INTEGER
    watched_runtime = movie_details['runtime']
    # INTEGER
    watched_release_date = movie_details['release_date']

    # GET MOVIE'S GENRE AND CONVERT TO STRING FOR STORING IN WATCHED TABLE
    movie_genres = movie_details['genres']
    movie_genres_list = []

    for genre in movie_genres:

        movie_genres_list.append(genre['name'])

    watched_genres = ",".join(movie_genres_list)

    # GET MOVIE'S CAST AND CONVERT TO STRING FOR STORING IN WATCHED TABLE

    # IF THE MOVIE HAS A PARTICULARLY LONG CAST, WE ONLY WANT THE FIRST 30 ACTORS
    if len(movie_credits['cast']) > 30:

        movie_cast = movie_credits['cast'][:30]

    else:
        movie_cast = movie_credits['cast']

    movie_cast_list = []
    for actor in movie_cast:

        movie_cast_list.append(actor['name'])

    watched_cast = ",".join(movie_cast_list)

    return render_template('movie_info.html',
                           movie_details=movie_details,
                           directed_by=directed_by,
                           movie_info_cast=movie_info_cast,
                           runtime=runtime_formatted,
                           rating_descriptions=rating_descriptions,
                           average_rating=average_rating,
                           user_rating=user_rating,
                           watched_movies=watched_movies,
                           saved_movies=saved_movies,
                           rated_movies=rated_movies,
                           movie_collection=movie_collection,
                           movie_recommendations=movie_recommendations,
                           collection_title=collection_title,
                           watched_runtime=watched_runtime,
                           watched_release_date=watched_release_date,
                           watched_cast=watched_cast,
                           watched_genres=watched_genres)


@app.route('/watched-movies', methods=['GET', 'POST'])
def watched():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    # IF THE USER SUBMITS THE SORT BY FORM
    if request.method == 'POST':

        if request.form['sort'] == 'date':

            cur = mysql.connection.cursor()
            watched_results = cur.execute(
                "SELECT w.movie_id, w.movie_title, w.poster_path, r.rating_score FROM user_watched w LEFT JOIN user_rated r ON w.user_id = r.user_id and w.movie_id = r.movie_id WHERE w.user_id = %s GROUP BY w.movie_id ORDER BY w.date_added DESC", (session['USER_ID'],))
            if watched_results > 0:

                watched_movies = cur.fetchall()

            else:
                watched_movies = None

            cur.close()
            sort = "date"

            return render_template('watched.html', watched_movies=watched_movies, sort=sort)

        elif request.form['sort'] == 'rating':

            cur = mysql.connection.cursor()
            watched_results = cur.execute(
                "SELECT w.movie_id, w.movie_title, w.poster_path, r.rating_score FROM user_watched w LEFT JOIN user_rated r ON w.user_id = r.user_id and w.movie_id = r.movie_id WHERE w.user_id = %s GROUP BY w.movie_id ORDER BY r.rating_score DESC", (session['USER_ID'],))

            if watched_results > 0:

                watched_movies = cur.fetchall()

            else:
                watched_movies = None

            cur.close()
            sort = "rating"

            return render_template('watched.html', watched_movies=watched_movies, sort=sort)

    cur = mysql.connection.cursor()
    watched_results = cur.execute(
        "SELECT w.movie_id, w.movie_title, w.poster_path, r.rating_score FROM user_watched w LEFT JOIN user_rated r ON w.user_id = r.user_id and w.movie_id = r.movie_id WHERE w.user_id = %s GROUP BY w.movie_id ORDER BY w.date_added DESC", (session['USER_ID'],))
    if watched_results > 0:

        watched_movies = cur.fetchall()

    else:
        watched_movies = None

    cur.close()
    sort = "date"

    return render_template('watched.html', watched_movies=watched_movies, sort=sort)


@app.route('/remove-from-watched/<int:movie_id>')
def remove_from_watched(movie_id):

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    # REMOVE CURRENT MOVIE FROM USER'S WATCHED MOVIES
    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_watched WHERE (user_id = %s AND movie_id = %s)",
                (session['USER_ID'], movie_id))
    mysql.connection.commit()
    cur.close()

    # CHECK IF USER HAS RATED THIS MOVIE, IF SO, DELETE THE RATING
    cur = mysql.connection.cursor()
    rated_results = cur.execute(
        "SELECT movie_id FROM user_rated WHERE user_id = %s", (session['USER_ID'],))

    if rated_results > 0:

        rated_results = cur.fetchall()
        cur.close()
        rated_movies = []

        for movie in rated_results:

            rated_movies.append(movie['movie_id'])

        if movie_id in rated_movies:

            cur = mysql.connection.cursor()
            cur.execute("DELETE FROM user_rated WHERE (user_id = %s AND movie_id = %s)",
                        (session['USER_ID'], movie_id))
            mysql.connection.commit()
            cur.close()
    else:
        cur.close()

    flash('Movie successfully removed from your watched movies!', 'success')
    return redirect(url_for('watched'))


@app.route('/remove-from-saved/<int:movie_id>')
def remove_from_saved(movie_id):

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    cur.execute("DELETE FROM user_saved WHERE (user_id = %s AND movie_id = %s)",
                (session['USER_ID'], movie_id))
    mysql.connection.commit()
    cur.close()

    flash('Movie successfully removed from your saved movies!', 'success')
    return redirect(url_for('saved'))


@app.route('/saved-movies')
def saved():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    cur = mysql.connection.cursor()
    saved_results = cur.execute(
        "SELECT movie_id, movie_title, poster_path FROM user_saved WHERE user_id = %s ORDER BY date_added DESC", (session['USER_ID'],))
    if saved_results > 0:

        saved_movies = cur.fetchall()

    else:
        saved_movies = None

    cur.close()

    return render_template('saved.html', saved_movies=saved_movies)


@app.route('/recommendations')
def recommendations():

    if 'USER_ID' not in session:

        session['FORM_NAME'] = "login"
        flash('Please log-in!', 'info')
        return redirect(url_for('index'))

    # STEP 1 - GET USERS TOP 10 RATED MOVIES WITH SCORE OF 4 OR GREATER, ORDER BY SCORE AND DATE ADDED
    cur = mysql.connection.cursor()
    user_top_rated = cur.execute(
        "SELECT movie_id FROM user_rated WHERE user_id = %s AND rating_score >= 4 ORDER BY rating_score DESC, date_added DESC LIMIT 10", (session['USER_ID'],))

    if user_top_rated > 0:

        user_top_rated = cur.fetchall()
        cur.close()
        top_rated_movies = []

        for movie in user_top_rated:

            top_rated_movies.append(movie['movie_id'])

        recommendations = []
        recommendations_check = []

        for top_rated_movie in top_rated_movies:

            # STEP 3 - CHECK IF USER SPECIFIED WHAT THEY LIKED ABOUT THE MOVIE WHEN THEY RATED IT

            cur = mysql.connection.cursor()
            cur.execute("SELECT liked FROM user_rated WHERE user_id = %s AND movie_id = %s",
                        (session['USER_ID'], top_rated_movie))
            liked = cur.fetchone()
            cur.close()

            if liked['liked']:

                liked_aspects = liked['liked'].split(',')

                # RECOMMENDATIONS WILL INITIALLY  BE GENERATED BY USING THE API REQUEST
                # FOR GENERAL RECOMMENDATIONS FOR THE SPECIFIED MOVIE
                recommendations_url = "https://api.themoviedb.org/3/movie/" + \
                    str(top_rated_movie) + "/recommendations?api_key=" + \
                    api_key + "&language=en-US&page=1"
                recommendations_request = requests.get(
                    recommendations_url, verify=False)

                for movie in json.loads(recommendations_request.text)['results'][:5]:

                    if movie['id'] not in recommendations_check:

                        recommendations.append(movie)
                        recommendations_check.append(movie['id'])

                # WE THEN ADD MOVIES TO THIS RECOMMENDATION LIST BASED ON THE ASPECTS THE USER LIKED
                for aspect in liked_aspects:

                    if aspect == 'acting':

                        # GET MOVIE CREDITS REQUEST
                        credits_url = 'https://api.themoviedb.org/3/movie/' + \
                            str(top_rated_movie) + '/credits?api_key=' + \
                            api_key + '&language=en-US'
                        credits_request = requests.get(
                            credits_url, verify=False)
                        movie_cast = json.loads(credits_request.text)['cast']

                        # GET LIST OF MOVIES FEATURING THE 3 MAIN ACTORS

                        # ACTOR 1
                        with_actor_1_url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + \
                            "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1&with_cast=" + \
                            str(movie_cast[0]['id'])
                        with_actor_1_request = requests.get(
                            with_actor_1_url, verify=False)
                        with_actor_1_movies = json.loads(
                            with_actor_1_request.text)['results']

                        for with_actor_1_movie in with_actor_1_movies:

                            if with_actor_1_movie['id'] not in recommendations_check:

                                recommendations.append(with_actor_1_movie)
                                recommendations_check.append(
                                    with_actor_1_movie['id'])

                        # ACTOR 2
                        with_actor_2_url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + \
                            "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1&with_cast=" + \
                            str(movie_cast[1]['id'])
                        with_actor_2_request = requests.get(
                            with_actor_2_url, verify=False)
                        with_actor_2_movies = json.loads(
                            with_actor_2_request.text)['results']

                        for with_actor_2_movie in with_actor_2_movies:

                            if with_actor_2_movie['id'] not in recommendations_check:

                                recommendations.append(with_actor_2_movie)
                                recommendations_check.append(
                                    with_actor_2_movie['id'])

                        # ACTOR 3
                        with_actor_3_url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + \
                            "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1&with_cast=" + \
                            str(movie_cast[2]['id'])
                        with_actor_3_request = requests.get(
                            with_actor_3_url, verify=False)
                        with_actor_3_movies = json.loads(
                            with_actor_3_request.text)['results']

                        for with_actor_3_movie in with_actor_3_movies:

                            if with_actor_3_movie['id'] not in recommendations_check:

                                recommendations.append(with_actor_3_movie)
                                recommendations_check.append(
                                    with_actor_3_movie['id'])

                    if aspect == 'directing':

                        credits_url = 'https://api.themoviedb.org/3/movie/' + \
                            str(top_rated_movie) + '/credits?api_key=' + \
                            api_key + '&language=en-US'
                        credits_request = requests.get(
                            credits_url, verify=False)
                        movie_crew = json.loads(credits_request.text)['crew']

                        for crew_member in movie_crew:

                            if crew_member['job'] == "Director":

                                director_id = crew_member['id']

                            else:
                                director_id = None

                        # GET LIST OF MOVIES WITH SAME DIRECTOR

                        if director_id:

                            with_director_url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + \
                                "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1&with_crew=" + \
                                str(director_id)
                            with_director_request = requests.get(
                                with_director_url, verify=False)
                            with_director_movies = json.loads(
                                with_director_request.text)['results']

                            for with_director_movie in with_director_movies:

                                if with_director_movie['id'] not in recommendations_check:

                                    recommendations.append(with_director_movie)
                                    recommendations_check.append(
                                        with_director_movie['id'])

                    if aspect == 'cinematography':

                        credits_url = 'https://api.themoviedb.org/3/movie/' + \
                            str(top_rated_movie) + '/credits?api_key=' + \
                            api_key + '&language=en-US'
                        credits_request = requests.get(
                            credits_url, verify=False)
                        movie_crew = json.loads(credits_request.text)['crew']

                        for crew_member in movie_crew:

                            if crew_member['job'] == "Director of Photography":

                                cinematographer_id = crew_member['id']

                            else:
                                cinematographer_id = None

                        # GET LIST OF MOVIES WITH SAME CINEMATOGRAPHER

                        if cinematographer_id:

                            with_cinematographer_url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + \
                                "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1&with_crew=" + \
                                str(cinematographer_id)
                            with_cinematographer_request = requests.get(
                                with_cinematographer_url, verify=False)
                            with_cinematographer_movies = json.loads(
                                with_cinematographer_request.text)['results']

                            for with_cinematographer_movie in with_cinematographer_movies:

                                if with_cinematographer_movie['id'] not in recommendations_check:

                                    recommendations.append(
                                        with_cinematographer_movie)
                                    recommendations_check.append(
                                        with_cinematographer_movie['id'])

                    if aspect == 'sound':

                        credits_url = 'https://api.themoviedb.org/3/movie/' + \
                            str(top_rated_movie) + '/credits?api_key=' + \
                            api_key + '&language=en-US'
                        credits_request = requests.get(
                            credits_url, verify=False)
                        movie_crew = json.loads(credits_request.text)['crew']

                        for crew_member in movie_crew:

                            if crew_member['job'] == "Original Music Composer":

                                composer_id = crew_member['id']

                            else:
                                composer_id = None

                        # GET LIST OF MOVIES WITH SAME COMPOSER

                        if composer_id:

                            with_composer_url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + \
                                "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1&with_crew=" + \
                                str(composer_id)
                            with_composer_request = requests.get(
                                with_composer_url, verify=False)
                            with_composer_movies = json.loads(
                                with_composer_request.text)['results']

                            for with_composer_movie in with_composer_movies:

                                if with_composer_movie['id'] not in recommendations_check:

                                    recommendations.append(with_composer_movie)
                                    recommendations_check.append(
                                        with_composer_movie['id'])

                    if aspect == 'theme' or 'genre':

                        # GET SIMILAR MOVIE REQUEST
                        similar_url = "https://api.themoviedb.org/3/movie/" + \
                            str(top_rated_movie) + "/similar?api_key=" + \
                            api_key + "&language=en-US&page=1"
                        similar_request = requests.get(
                            similar_url, verify=False)
                        similar_movies = json.loads(
                            similar_request.text)['results']

                        for similar_movie in similar_movies:

                            if similar_movie['id'] not in recommendations_check:

                                recommendations.append(similar_movie)
                                recommendations_check.append(
                                    similar_movie['id'])

                    if aspect == 'writing':

                        credits_url = 'https://api.themoviedb.org/3/movie/' + \
                            str(top_rated_movie) + '/credits?api_key=' + \
                            api_key + '&language=en-US'
                        credits_request = requests.get(
                            credits_url, verify=False)
                        movie_crew = json.loads(credits_request.text)['crew']

                        for crew_member in movie_crew:

                            if crew_member['job'] == "Screenplay":

                                writer_id = crew_member['id']

                            else:

                                writer_id = None

                        # GET LIST OF MOVIES WITH SAME WRITER

                        if writer_id:

                            with_writer_url = "https://api.themoviedb.org/3/discover/movie?api_key=" + api_key + \
                                "&language=en-US&sort_by=popularity.desc&include_adult=false&include_video=false&page=1&with_crew=" + \
                                str(writer_id)
                            with_writer_request = requests.get(
                                with_writer_url, verify=False)
                            with_writer_movies = json.loads(
                                with_writer_request.text)['results']

                            for with_writer_movie in with_writer_movies:

                                if with_writer_movie['id'] not in recommendations_check:

                                    recommendations.append(with_writer_movie)
                                    recommendations_check.append(
                                        with_writer_movie['id'])

            else:

                # IF THE 'LIKED' COLUMN IS NULL
                # RECOMMENDATIONS WILL BE GENERATED BY USING THE API REQUEST FOR GENERAL RECOMMENDATIONS FOR THE SPECIFIED MOVIE
                recommendations_url = "https://api.themoviedb.org/3/movie/" + \
                    str(top_rated_movie) + "/recommendations?api_key=" + \
                    api_key + "&language=en-US&page=1"
                recommendations_request = requests.get(
                    recommendations_url, verify=False)

                for movie in json.loads(recommendations_request.text)['results']:

                    if movie['id'] not in recommendations_check:

                        recommendations.append(movie)
                        recommendations_check.append(movie['id'])

        # MYSQL CURSOR TO FETCH ALL USER'S WATCHED MOVIES
        cur = mysql.connection.cursor()
        watched_results = cur.execute(
            "SELECT movie_id FROM user_watched WHERE user_id = %s", (session['USER_ID'],))
        if watched_results > 0:

            watched_results = cur.fetchall()
            watched_movies = []

            for movie in watched_results:

                watched_movies.append(movie['movie_id'])

        else:
            watched_movies = None

        cur.close()

        return render_template('recommendations.html',
                               recommendations=recommendations,
                               watched_movies=watched_movies)

    else:
        cur.close()
        return render_template('recommendations.html')


@app.route('/logout')
def logout():

    session.clear()
    session['FORM_NAME'] = 'login'

    flash('Logout Successfull!', 'success')
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=True)
