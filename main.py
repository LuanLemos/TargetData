# Test for TargetData.

from flask import Flask, make_response, jsonify, request
from flask_jwt_extended import JWTManager, create_access_token, jwt_required
from bduser import collection
import requests
import xml.etree.ElementTree as ET
from unidecode import unidecode
import logging
from logging.handlers import RotatingFileHandler
from elasticsearch import Elasticsearch
from flask import send_file

app = Flask('TargetData')
app.config['JWT_SECRET_KEY'] = '9213' # JWT.
jwt = JWTManager(app)

# ElasticSearch config
es = Elasticsearch ([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])

# Logging config
handler = RotatingFileHandler('app.log', maxBytes=10000, backupCount=1)
handler.setLevel(logging.INFO)
app.logger.addHandler(handler)

@app.route('/users', methods=['POST']) # Creating user and storing in DB
def create_user():
    data = request.json
    user = data.get('user')
    password = data.get('password')

    if not user or not password:
        return make_response(jsonify({"error": "User and password are required."}), 400)

    new_user = {"User:": user, "Password:": password}
    collection.insert_one(new_user)

    app.logger.info('Created user: %s', user)

    return make_response(jsonify({"Message:": "Created user successfully"}), 201)

@app.route('/login', methods=['POST']) # login method to create access token in DB
def login():
    data = request.json
    user = data.get('user')
    password = data.get ('password')

    user_data = collection.find_one({"user": user, "password": password})

    if user_data:
        access_token = create_access_token(identity=user)

        app.logger.info('Logged in user: %s', user)

        return jsonify (access_token=access_token)
    else:
        app.logger.info('Failed login attempt for user: %s', user)

        return make_response (jsonify({"error": "Invalid Credentials"}), 401)

@app.route('/weather', methods=['POST'])
@jwt_required() # Requiring access point token
def weather():
    cep = request.json.get('cep')

    via_cep_url = f'https://viacep.com.br/ws/{cep}/json/'
    response_via_cep = requests.get(via_cep_url)
    via_cep_data = response_via_cep.json()

    city = via_cep_data.get ('localidade')
    city = unidecode(city)

    app.logger.info('Weather forecast requested for city: %s', city)
    
    inpe_url = f'http://servicos.cptec.inpe.br/XML/listaCidades?city={city}'

    response_inpe = requests.get(inpe_url)
    root = ET.fromstring(response_inpe.content)
    
    cidade = root.find('.//cidade')
    if cidade is not None:
        city_id = cidade.find('id').text
        print ("city id:", city_id)
    else:
        print ("Nenhuma cidade encontrada no XML.")

    inpeprev_url = f'http://servicos.cptec.inpe.br/XML/cidade/{city_id}/previsao.xml'
    response_inpeprev = requests.get(inpeprev_url)
    weather_forecast = process_weather_xml(response_inpeprev.text)


    return jsonify({
        "via_cep_data": via_cep_data,
        "weather_forecast": weather_forecast
    })

def process_weather_xml(xml_data):
    root = ET.fromstring(xml_data)
    weather_forecast = []
    for day in root.iter('previsao'):
        weather_data = {
            'dia': day.find('dia').text,
            'tempo': day.find('tempo').text,
            'maxima': day.find('maxima').text,
            'minima': day.find('minima').text,
            'iuv': day.find('iuv').text
        }
        weather_forecast.append(weather_data)
    return weather_forecast

@app.route('/logs', methods=['GET'])
@jwt_required()
def get_logs():
    try:
        with open('app.log', 'r') as file:
            logs = file.read()
        return logs, 200
    except Exception as e:
        return jsonify({"error": "Failed to retrieve logs."}), 500

@app.route('/protected', methods=['GET'])
@jwt_required() # Requiring access point token
def protected():
    return jsonify({"message": "This is a protected endpoint!"})


app.run()
