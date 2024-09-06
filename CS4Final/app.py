from flask import Flask, render_template, request, redirect, url_for, session
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import requests
app = Flask(__name__)
app.config['MYSQL_HOST'] = 'mysql.2122.lakeside-cs.org'
app.config['MYSQL_USER'] = 'student2122'
app.config['MYSQL_PASSWORD'] = 'm545CS42122'
app.config['MYSQL_DB'] = '2122project'
app.config['MYSQL_CURSORCLASS'] = 'DictCursor'
app.config['SECRET_KEY'] = 'plmoknijifef'
mysql = MySQL(app)

@app.route('/')
def index():
    return render_template('index.html.j2', username=session.get('jerrychen_username'))

@app.route('/login', methods=['GET','POST'])
def login():
    #all login and login related code is taken from the secure login mini-lesson on haiku
    if request.method == 'GET':
        return render_template('login.html.j2', error=request.args.get('error'), username=session.get('jerrychen_username'))
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        cursor = mysql.connection.cursor()
        query = 'SELECT password FROM jerrychen_login WHERE username=%s'
        queryVars = (username,)
        cursor.execute(query, queryVars)
        mysql.connection.commit()
        results = cursor.fetchall()
        if (len(results) == 1):
            hashedPassword = results[0]['password']
            if check_password_hash(hashedPassword, password):
                session['jerrychen_username'] = username
                return redirect(url_for('index'))
            else:
                return redirect(url_for('login', error=True))
        else:
            return redirect(url_for('login', error=True))

@app.route('/signup', methods=['GET','POST'])
def signup():
    #signup related code is from the secure login mini lesson on haiku
    if request.method == 'GET':
        return render_template('signup.html.j2', error=request.args.get('error'), username=session.get('jerrychen_username'))
    else:
        username = request.form.get('username')
        password = request.form.get('password')
        email = request.form.get('email')
        securedPassword = generate_password_hash(password)
        cursor = mysql.connection.cursor()
        check = checkUser(cursor, username)
        #check if this email belongs to lakeside
        checkEmail = "@lakesideschool.org" in email
        #different error numbers correspond to the different errors, see signup.html.j2
        if check == False:
            return redirect(url_for('signup', error=1))
        elif len(username) < 1 or len(password) < 1:
            return redirect(url_for('signup', error=2))
        elif len(email) < 1 or checkEmail == False:
            return redirect(url_for('signup', error=3))
        else:
            query = 'INSERT INTO jerrychen_login(username, password, email) VALUES (%s, %s, %s)'
            queryVars = (username,securedPassword,email,)
            cursor.execute(query, queryVars)
            mysql.connection.commit()
            return redirect(url_for('login'))

@app.route('/logout')
def logout():
    session.pop('jerrychen_username', None)
    return redirect(url_for('index'))

@app.route('/search')
def search():
    return render_template('search.html.j2', username=session.get('jerrychen_username'))

@app.route('/results', methods=['POST'])
def results():
    genres = genreList()
    if listEmpty(genres):
        search = searchQuery(genres)
        cursor = mysql.connection.cursor()
        #orders result by rating from highest to low
        query = 'SELECT * FROM jerrychen_movies WHERE ' + search + ' ORDER BY rating DESC;'
        cursor.execute(query)
        mysql.connection.commit()
        result = cursor.fetchall()
        return render_template('results.html.j2', username=session.get('jerrychen_username'), results = result, valid = True)
    else:
        return render_template('results.html.j2', username=session.get('jerrychen_username'), valid = False)

@app.route('/add')
def add():
    return render_template('add.html.j2', username=session.get('jerrychen_username'))

@app.route('/newMovie', methods=['POST'])
def newMovie():
    name = str(request.form.get('movie'))
    rec = str(request.form.get('rec'))
    rating = request.form.get('rating')
    response = requests.get("https://www.omdbapi.com/?t=" + str(name) + "&apikey=f4f70034")
    answer = response.json()
    genreValue = genreList()
    #sets an empty recommendation to automatically equal "N/A" so it looks good
    if rec == " ":
        rec = "N/A"
    #api will auto return False as response if they couldn't find a movie with the title listed
    #different error numbers correspond to different error messages that are displayed
    if answer["Response"] == 'False':
        return render_template('newMovie.html.j2', username=session.get('jerrychen_username'), error = 1)
    elif checkTitle(answer["Title"]) == False:
        return render_template('newMovie.html.j2', username=session.get('jerrychen_username'), error = 2)
    elif rating == "" or float(rating) < 1 or float(rating) > 10:
        return render_template('newMovie.html.j2', username=session.get('jerrychen_username'), error = 3)
    else:
        addMovie(answer, rec, float(rating), genreValue)
        return render_template('newMovie.html.j2', username=session.get('jerrychen_username'), error = 0, rec = rec)

#returns the checkboxes checked as a list of true and false statements in the order of a list containing all genres
def genreList():
    genres = ['action', 'sci', 'fantasy', 'horror', 'drama', 'comedy', 'romance', 'animated', 'thriller']
    genreValue = []
    for x in genres:
        if request.form.get(x) != None:
            genreValue.append(True)
        else:
            genreValue.append(False)
    return genreValue

#checks if the genre list is all false or not
def listEmpty(list):
    for x in list:
        if x:
            return True
    return False

#checks if username is taken
def checkUser(cursor, username):
    query = 'SELECT * FROM jerrychen_login WHERE username = %s'
    queryVars = (username,)
    cursor.execute(query, queryVars)
    mysql.connection.commit()
    result = cursor.fetchall()
    return len(result) == 0

#checks if movie has already been added into database
def checkTitle(movie):
    cursor = mysql.connection.cursor()
    query = 'SELECT * FROM jerrychen_movies WHERE title = %s'
    queryVars = (movie,)
    cursor.execute(query, queryVars)
    mysql.connection.commit()
    result = cursor.fetchall()
    return len(result) == 0

#creates searchQuery based on inputted list
def searchQuery(results):
    genres = ['action', 'sci', 'fantasy', 'horror', 'drama', 'comedy', 'romance', 'animated', 'thriller']
    search = ""
    i = 0
    for x in genres:
        if results[i]:
            search = search + str(genres[i]) + " = 1" + " OR "
        i = i + 1
    #takes the query string and takes off the extra " OR " for the last part
    if len(search) > 0:
        search = search[0:len(search)-4]
    return search

#adds movie to database
def addMovie(answer, rec, rating, genreValue):
    cursor = mysql.connection.cursor()
    query = 'INSERT INTO jerrychen_movies(title, description, recommend, img, rating, action, sci, fantasy, horror, drama, comedy, romance, animated, thriller) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s)'
    queryVars = (answer["Title"], answer["Plot"], rec, answer["Poster"], rating, genreValue[0], genreValue[1], genreValue[2], genreValue[3], genreValue[4], genreValue[5], genreValue[6], genreValue[7], genreValue[8])
    cursor.execute(query, queryVars)
    mysql.connection.commit()
