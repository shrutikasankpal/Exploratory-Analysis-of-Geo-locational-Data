# import the necessary packages
from flask import Flask, render_template, redirect, url_for, request,session,Response,send_file
from werkzeug import secure_filename
import os
import cv2
import pandas as pd
import sqlite3
from datetime import datetime
from autocorrect import Speller
import json
from geopy.geocoders import Nominatim
import folium
from dataProcessing import *

geolocator = Nominatim(user_agent="traffic_control")

lat = 0
lon = 0

email = ''
loc = ''
name = ''

app = Flask(__name__)

app.secret_key = '1234'
app.config["CACHE_TYPE"] = "null"
app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 0

@app.route('/', methods=['GET', 'POST'])
def landing():
	return redirect(url_for('login'))

@app.route('/login', methods=['GET', 'POST'])
def login():
	error = None
	global name
	global email
	if request.method == 'POST':
		email = request.form['email']
		password = request.form['password']
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute(f"SELECT Name from Users WHERE Email='{email}' AND password = '{password}';")
		try:
			name = cursorObj.fetchone()[0]
			return redirect(url_for('home'))
		except:
			error = "Invalid Credentials Please try again..!!!"
			return render_template('login.html',error=error)
	return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
	error = None
	if request.method == 'POST':
		if request.form['sub']=='Submit':
			name = request.form['name']
			email = request.form['email']
			password = request.form['password']
			rpassword = request.form['rpassword']
			pet = request.form['pet']
			if(password != rpassword):
				error='Password dose not match..!!!'
				return render_template('register.html',error=error)
			try:
				con = sqlite3.connect('mydatabase.db')
				cursorObj = con.cursor()
				cursorObj.execute(f"SELECT Name from Users WHERE Email='{email}' AND password = '{password}';")
			
				if(cursorObj.fetchone()):
					error = "User already Registered...!!!"
					return render_template('register.html',error=error)
			except:
				pass
			now = datetime.now()
			dt_string = now.strftime("%d/%m/%Y %H:%M:%S")			
			con = sqlite3.connect('mydatabase.db')
			cursorObj = con.cursor()
			cursorObj.execute("CREATE TABLE IF NOT EXISTS Users (Date text,Name text,Email text,password text,pet text)")
			cursorObj.execute("INSERT INTO Users VALUES(?,?,?,?,?)",(dt_string,name,email,password,pet))
			con.commit()

			return redirect(url_for('login'))

	return render_template('register.html')

@app.route('/forgot', methods=['GET', 'POST'])
def forgot():
	error = None
	global name
	if request.method == 'POST':
		email = request.form['email']
		pet = request.form['pet']
		con = sqlite3.connect('mydatabase.db')
		cursorObj = con.cursor()
		cursorObj.execute(f"SELECT password from Users WHERE Email='{email}' AND pet = '{pet}';")
		
		try:
			password = cursorObj.fetchone()
			#print(password)
			error = "Your password : "+password[0]
		except:
			error = "Invalid information Please try again..!!!"
		return render_template('forgot-password.html',error=error)
	return render_template('forgot-password.html')

@app.route('/home', methods=['GET', 'POST'])
def home():
	global name
	return render_template('home.html',name=name)

@app.route('/dashboard', methods=['GET', 'POST'])
def dashboard():
	return render_template('dashboard.html',name=name)

@app.route('/location',methods=['GET', 'POST'])
def location():
	global lat
	global lon
	global loc
	if request.method == 'POST':
		name = request.form['name']
		loc = name
		location = geolocator.geocode(name)
		result = "Lattitude = "+str(location.latitude) + ", " + "Longitude = " + str(location.longitude)
		my_map = folium.Map(location=[location.latitude,location.longitude], zoom_start=14)
		folium.Marker([location.latitude,location.longitude],popup = name).add_to(my_map)
		my_map.save("map.html ")
		lat = location.latitude
		lon = location.longitude
		return render_template('location.html',result=result,address=location.address)
	return render_template('location.html')

@app.route('/map')
def map():
	return send_file('templates/map.html')

@app.route('/locmap')
def locmap():
	return render_template('locmap.html')
	#return send_file('templates/locmap.html')

@app.route('/clustering', methods=['GET', 'POST'])
def clustering():
	global lat
	global lon
	global loc
	global name
	get_locationData(lat,lon,loc)
	df = pd.read_csv('cleaned_apartment.csv')
	return render_template('clustering.html',name=name,tables=[df.to_html(classes='table-responsive table table-bordered table-hover')], titles=df.columns.values)

@app.route('/givefeedback', methods=['GET', 'POST'])
def givefeedback():
	global name
	global email
	if request.method == 'POST':
		if request.form['sub']=='Rate':
			rating = request.form['rate']
			suggestion = request.form['suggestions']
			now = datetime.now()
			dt_string = now.strftime("%d/%m/%Y %H:%M:%S")

			con = sqlite3.connect('mydatabase.db')
			cursorObj = con.cursor()
			cursorObj.execute("CREATE TABLE IF NOT EXISTS Feedback (Date text,Name text,Contact text,Ratings text,Feedback text)")
			cursorObj.execute("INSERT INTO Feedback VALUES(?,?,?,?,?)",(dt_string,name,email,rating,suggestion))
			con.commit()
			return redirect(url_for('home'))
	return render_template('givefeedback.html',name=name)

@app.route('/feedback', methods=['GET', 'POST'])
def feedback():
	global name
	conn = sqlite3.connect('mydatabase.db', isolation_level=None,
						detect_types=sqlite3.PARSE_COLNAMES)
	df = pd.read_sql_query(f"SELECT * from Feedback WHERE Name='{name}';", conn)
	
	return render_template('feedback.html',name=name,tables=[df.to_html(classes='table-responsive table table-bordered table-hover')], titles=df.columns.values)


# No caching at all for API endpoints.
@app.after_request
def add_header(response):
	# response.cache_control.no_store = True
	response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate, post-check=0, pre-check=0, max-age=0'
	response.headers['Pragma'] = 'no-cache'
	response.headers['Expires'] = '-1'
	return response


if __name__ == '__main__' and run:
	app.run(host='0.0.0.0', debug=True, threaded=True)
