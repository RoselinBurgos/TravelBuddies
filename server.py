from flask import Flask, render_template, request, redirect, session, flash
from mysqlconnection import connectToMySQL
from time import strftime, localtime
from flask_bcrypt import Bcrypt 
from datetime import datetime
from datetime import date
import re
app = Flask(__name__)
bcrypt = Bcrypt(app)
app.secret_key = 'TheSecretKey'
EMAIL_REGEX = re.compile(r'^[a-zA-Z0-9\.\+_-]+@[a-zA-Z0-9\._-]+\.[a-zA-Z]*$')


mysql = connectToMySQL('buddies')
print("all the users", mysql.query_db("SELECT * FROM users;"))

@app.route('/')
def index():

    mysql = connectToMySQL("buddies")
    all_users = mysql.query_db("SELECT * FROM users")
    print("Fetched all users", all_users)
    return render_template('index.html', all_users=all_users)

@app.route('/result', methods=['POST'])
def result():

    passFlag = False
    if len(request.form['first_name']) ==0:
        flash('Invalid first name','wrong')
        passFlag = True

    if not request.form['first_name'].isalpha():
        flash('First name has non-alpha character','wrong')
        passFlag = True

    if len(request.form['last_name']) < 1:
        flash('Invalid last name','wrong')
        passFlag = True

    if not request.form['last_name'].isalpha():
        flash('Last name has a non-alpha character','wrong')
        passFlag = True

    if len(request.form['email']) < 1:
        flash('Invalid email','wrong')
        passFlag = True
    elif not EMAIL_REGEX.match(request.form['email']):
        flash('Invalid email format','wrong')
        passFlag = True

    if len(request.form['password']) < 8:
        flash('Password must contain at least 8 characters', 'wrong')
        passFlag = True

    if request.form['password'] != request.form['c_password']:
        flash('Password does not match','wrong')
        passFlag = True

    if passFlag == True:
        return redirect('/')
    else:
        passcrypt = bcrypt.generate_password_hash(request.form['password'])
  

        mysql = connectToMySQL("buddies")
        query = "INSERT INTO users (email,first_name, last_name, password,created_at,updated_at) VALUES (%(email)s,%(first_name)s, %(last_name)s, %(password)s,NOW(),NOW());"
        data = {
                'email': request.form['email'],
                'first_name': request.form['first_name'],
                'last_name':  request.form['last_name'],
                'password': passcrypt
                }
        user_id= mysql.query_db(query, data)
        session['id'] = user_id
        

        flash('Registartion Complete! You may now Login.', 'okgreen')
        return redirect('/')

@app.route('/login', methods=['POST'])
def login():
    
    mysql = connectToMySQL("buddies")
    query = "SELECT * From users WHERE email = %(email)s"
    data = {
            'email': request.form['email']
            }
    users = mysql.query_db(query,data)

    if len(users) == 0:
        flash("INVALID CREDENTIALS",'wrong')
        return redirect('/')
    user = users[0]
    if bcrypt.check_password_hash(user['password'], request.form['password']):
        session['id'] = user['id']
        session['first_name'] = user['first_name'] 
        return redirect('/travels')
    else: 
        flash("INVALID CREDENTIALS",'wrong')
    return redirect('/')



@app.route('/travels')
def home_index():

    if not 'id' in session:
        return redirect ('/')

    # all trips I have created
    mysql = connectToMySQL('buddies')
    data = {
        "user_id" : session['id']
    }
    query = "SELECT * FROM travel WHERE user_id = %(user_id)s;"
    traveler = mysql.query_db(query,data)

    # all trips I have joined
    mysql = connectToMySQL('buddies')
    query = "SELECT * FROM users JOIN joins ON users.id = joins.user_id JOIN travel ON joins.travel_id = travel.id WHERE users.id= %(user_id)s;"
    data = {
        "user_id" : session['id'],
            }
    my_joined_trips = mysql.query_db(query,data)
    
    mysql2 = connectToMySQL('buddies')
    query = "SELECT * FROM travel WHERE user_id != %(user_id)s;"
    other_trips = mysql2.query_db(query,data)
    
    return render_template('index2.html',traveler=traveler, other_trips=other_trips,my_joined_trips=my_joined_trips)

@app.route('/delete_message/<int:travel_id>')
def del_msg(travel_id):

    mysql = connectToMySQL('buddies')
    query = "DELETE FROM joins where travel_id = %(travel_id)s"
    data = {
            'travel_id':travel_id,
        }
    mysql.query_db(query,data)

    mysql = connectToMySQL('buddies')
    query = "DELETE FROM travel where id = %(travel_id)s"
    data = {
            'travel_id':travel_id,
        }
    mysql.query_db(query,data)
    return redirect('/travels')


@app.route('/addtrip')
def add():

    if not 'id' in session:
        return redirect ('/')
    return render_template('/add.html')

@app.route('/adding', methods=['POST'])
def adding():
    the_date_start = None
    the_date_end = None


    passFlag = False
    if len(request.form['destination']) ==0:
        flash('Destination must not be blank','wrong')
        passFlag = True

    if len(request.form['description']) < 1:
        flash('Description must not be blank','wrong')
        passFlag = True

    if request.form['startdate'] != "":
        the_date_start = datetime.strptime(request.form['startdate'], '%Y-%m-%d') 
    else:
        flash('Travel Date From must not be blank','wrong')
        passFlag = True

    if request.form['enddate'] != "":
        the_date_end = datetime.strptime(request.form['enddate'], '%Y-%m-%d') 
    else:
        flash('Travel Date From must not be blank','wrong')
        passFlag = True

    if passFlag:
        return redirect('/addtrip')

    if the_date_start > the_date_end:
        flash('Return date can not be before departure date','wrong')
        passFlag = True

    if the_date_start < datetime.now():
        flash('You can not select a past date','wrong')
        passFlag = True

    if passFlag == True:
        return redirect('/addtrip')
    else:

        mysql = connectToMySQL('buddies')
        query = "INSERT INTO travel(user_id, destination, description, start_date,end_date, created_at, updated_at) VALUES (%(user_id)s,%(destination)s, %(description)s,%(start_date)s,%(end_date)s,NOW(),NOW());"
        data = {
                'user_id':session['id'],
                'destination': request.form['destination'],
                'description':  request.form['description'],
                'start_date': request.form['startdate'],
                'end_date': request.form['enddate'],
                }
        mysql.query_db(query, data)

    return redirect('travels')

@app.route('/view/<travel_id>')
def views(travel_id):
    if not 'id' in session:
        return redirect ('/')


    mysql = connectToMySQL("buddies")
    query = "Select * from users JOIN travel ON users.id = travel.user_id WHERE travel.id =%(travel_id)s;"
    data ={
            'travel_id' : travel_id
          }
    
    travel_inf = mysql.query_db(query, data)

    mysql = connectToMySQL('buddies')
    query = "SELECT * FROM users JOIN joins ON users.id = joins.user_id JOIN travel on joins.travel_id = travel.id WHERE travel_id = %(travel_id)s AND users.id !=  travel.user_id;"
    data = {
        "user_id" : session['id'],
        'travel_id' : travel_id
            }
    others_on_trip = mysql.query_db(query,data)
    return render_template('views.html', others_on_trip = others_on_trip, travel_inf = travel_inf)

@app.route('/join/<int:travel_id>')
def join_trip(travel_id):
    mysql = connectToMySQL('buddies')
    data = {
        "user_id" : session['id'],
        "travel_id" : travel_id
    }
    query = "SELECT * FROM joins WHERE user_id = %(user_id)s AND travel_id = %(travel_id)s;"
    joined_trip = mysql.query_db(query,data)

    if len(joined_trip) == 0:
        mysql = connectToMySQL('buddies')
        data = {
            "user_id" : session['id'],
            "travel_id" : travel_id
        }
        query = "INSERT INTO joins (user_id, travel_id) VALUES (%(user_id)s, %(travel_id)s);"
        mysql.query_db(query,data)

    return redirect('/travels')

@app.route('/remove/<int:travel_id>')
def cancel_trip(travel_id):
    mysql = connectToMySQL('buddies')
    data = {
        "travel_id" : travel_id,
        "user_id" : session['id']
    }
    query = "DELETE FROM joins WHERE travel_id = %(travel_id)s AND user_id = %(user_id)s;"
    mysql.query_db(query,data)
    return redirect('/travels')


@app.route('/logout')
def logout():
    session.clear()
    return redirect('/')

app.run(debug=True)