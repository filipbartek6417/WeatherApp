import os
import requests
import sys
import time

from flask import Flask, render_template, request, redirect, flash
from flask_sqlalchemy import SQLAlchemy

KELVIN = 273.15
APP = Flask(__name__)
APP.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:////tmp/cityWeather.db'
APP.secret_key = os.environ['FLASK_APP_SECRET_KEY']
DB = SQLAlchemy(APP)


class City(DB.Model):  # SQL Definition of the model for the DB
    id = DB.Column(DB.Integer, primary_key=True)
    name = DB.Column(DB.String(200), unique=True, nullable=False)


# City.query.delete()  # these 2 lines are used to clear the db
# db.session.commit()  # on the start of the app


def get_city_forecast(city):  # returns a dict for the template
    params = {'q': city, 'appid': os.environ['OPENWEATHER_API_KEY']}
    weather_request = requests.get('https://api.openweathermap.org/'
                                   'data/2.5/weather', params=params).json()
    if weather_request['cod'] == 200:  # if all went well (server issued a 200)
        local_time = time.gmtime().tm_hour + int(weather_request['timezone']) // 3600
        if 9 < local_time <= 17:  # determine what time it is in the region
            back_image = 'day'  # and set an appropriate image
        elif 20 < local_time <= 23 or 0 <= local_time < 6:
            back_image = 'night'
        else:
            back_image = 'evening-morning'
        return {
            'temperature': int(weather_request['main']['temp'] - KELVIN),
            'weather_type': weather_request['weather'][0]['main'],
            'city': weather_request['name'],
            'image': back_image
        }
    return None  # if city not found, return None


@APP.route('/', methods=['GET', 'POST'])
def add_city():
    all_forecasts = []
    for city in City.query.all():  # iterate through cities already in DB
        city_forecast = get_city_forecast(city.name)
        city_forecast['id'] = city.id
        all_forecasts.append(city_forecast)
    new_city = request.form.get('city_name', None)  # get user input from the form
    if new_city:
        new_city_forecast = get_city_forecast(new_city)
        if new_city_forecast:  # if the city exists
            if new_city_forecast['city'] not in [i['city'] for i in all_forecasts]:  # and is not in the DB already
                city = City(name=new_city_forecast['city'])
                DB.session.add(city)
                DB.session.commit()
                new_city_forecast['id'] = city.id
                all_forecasts.append(new_city_forecast)  # add to DB and save
            else:
                flash("The city has already been added to the list!")
        else:
            flash("The city doesn't exist!")
    return render_template('index.html', all_forecasts=all_forecasts)


@APP.route('/delete/<city_id>', methods=['GET', 'POST'])
def delete(city_id):  # deletes city on click on the cross of the city card
    city = City.query.filter_by(id=city_id).first()
    DB.session.delete(city)
    DB.session.commit()
    return redirect('/')


# Run flask
if __name__ == '__main__':
    if len(sys.argv) > 1:
        arg_host, arg_port = sys.argv[1].split(':')
        APP.run(host=arg_host, port=arg_port)
    else:
        APP.run()
