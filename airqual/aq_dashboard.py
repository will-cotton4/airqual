"""OpenAQ Air Quality Dashboard with Flask."""
import os
from os import getenv
from pickle import dump, loads
from flask import Flask, render_template, request, jsonify
from decouple import config
from flask_sqlalchemy import SQLAlchemy
import openaq

APP = Flask(__name__)
DB = SQLAlchemy(APP)


class Record(DB.Model):
    """Contains database schema for record of values taken from API call"""
    id = DB.Column(DB.Integer, primary_key=True)
    datetime = DB.Column(DB.String(25))
    value = DB.Column(DB.Float, nullable=False)

    def __repr__(self):
        return '<DATE: {}, VALUE: {}>'.format(self.datetime, self.value)


def create_app():
    """Contains routing logic for airqual app."""
    # APP = Flask(__name__)
    APP.config['ENV'] = config('ENV')
    APP.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
    api = openaq.OpenAQ()

    def process_to_list(body):
        """Processes API results into list of tuples."""
        results = body['results']
        utc_dates_values = []
        for result in results:
            result_tuple = (str(result['date']['utc']), result['value'])
            utc_dates_values.append(result_tuple)
        return utc_dates_values

    @APP.route('/')
    def root():
        """Main route."""
        potential_risks = Record.query.filter(Record.value >= 10).all()
        return render_template('base.html', records=potential_risks)

    @APP.route('/refresh')
    def refresh():
        """Pull fresh data from Open AQ and replace existing data."""
        DB.drop_all()
        DB.create_all()
        status, body = api.measurements(city='Los Angeles', parameter='pm25')
        new_data = process_to_list(body)
        for result in new_data:
            db_record = Record(datetime=result[0], value=result[1])
            DB.session.add(db_record)
        DB.session.commit()
        return 'Data refreshed!'

    return APP
