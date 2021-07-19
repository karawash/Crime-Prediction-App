from flask import Flask, request
from flask_restful import Resource, Api
from sqlalchemy import create_engine
from json import dumps
from flask.json import jsonify
from flask_cors import CORS
import json
from flasgger import Swagger

# install
# pip install flask flask-jsonpify flask-sqlalchemy flask-restful flask_cors flasgger

import sys, json, io, time
import pandas as pd
import numpy as np
from keras.models import model_from_json
from sklearn import preprocessing
from sklearn.preprocessing import LabelEncoder
from keras.utils import np_utils

app = Flask(__name__)
cors = CORS(app, resources={r"/api/*": {"origins": "*"}})
api = Api(app)

Swagger(app)

@app.route('/api/records', methods=['POST'])
def records_index(month=12, day=15, hour=6):
    """
    This API predict crime happens index 
    Call this api passing occurrence month, occurrence day, occurrence hour
    ---
    tags:
      - dasboard crime prediction
    parameters:
      - name: body
        in: body
        schema:
          id: Date and Period
          required:
            - month
            - day
            - hour
          properties:
             month:
                type: integer
                description: month
                default: 12
             day:               
                type: integer
                description: day
                default: 15
             hour:
                type: integer
                description: hour
                default: 6
    responses:
      200:
        description: The required result is available
      500:
        description: Error!
    """
    jsonObj = request.get_json()
    month = jsonObj.get('month')
    print(month)
    day = jsonObj.get('day')
    hour = jsonObj.get('hour')
    return records_prediction_handler(month, day, hour)

@app.route('/api/location', methods=['POST'])
def address_index(address = " 1 Yonge St, Ontario", month=12, day=15, hour=6):
    """
    This API predict crime index based on location address
    Call this api by passing address, occurrence month, occurrence day, occurrence hour
    ---
    tags:
      - address based crime prediction
    parameters:
      - name: body
        in: body
        schema:
          id: address, date and period
          required:
            - address
            - month
            - day
            - hour
          properties:
             month:
                type: string
                description: address
                default: 1 yonge street Ontario
             month:
                type: integer
                description: month
                default: 12
             day:               
                type: integer
                description: day
                default: 15
             hour:
                type: integer
                description: hour
                default: 6
    responses:
      200:
        description: The required result is available
      500:
        description: Error!
    """
    jsonObj = request.get_json()
    month = jsonObj.get('month')
    print(month)
    day = jsonObj.get('day')
    hour = jsonObj.get('hour')
    return records_prediction_handler(month, day, hour)


def records_prediction_handler(occurrencemonth, occurrenceday, occurrencehour):
    #create array for specific month and day and apply on 140 division
    x=[]
    y =[]
    for index in range(1,141):
        y.append([index])
    y = np.array(y)
    
    encoder = LabelEncoder()
    encoder.fit(y)
    y = encoder.transform(y)
    y = np_utils.to_categorical(y)

    for index in range(1,141):
        x.append([occurrencemonth,occurrenceday,occurrencehour])
    x = np.array(x)
    
    pred_x = np.concatenate((x, y),axis=1)
    #return prediction result on a day for 140 division as array
    predictions = loaded_model.predict_proba(pred_x)
    
    pred_store = pd.DataFrame(dict(f0=[],f1=[],f2=[],f3=[],f4=[],index=[],name=[],period=[], risk=[]), dtype=int)
    
    for value in range(0,140):
        pred_store= pred_store.append(dict(f0=round(predictions[value][0]*100, 2),f1= round(predictions[value][1]*100, 2),f2=round(predictions[value][2]*100, 2),f3=round(predictions[value][3]*100, 2),f4=round(predictions[value][4]*100, 2),index=round((1-predictions[value][5])*100, 2), name=hood(value)[value], h_id=str(value+1), period=getperiod(occurrencehour), risk=getrisk((1-predictions[value][5])*100)), ignore_index=True)
        
    #important to add the below line because it is needed on the front end
    pred_store.index += 1
    
    return pred_store.to_json(orient='records')

def hood(value):
    NB = NBList
    result = NB[NB.Hood_ID == value+1]
    #print(result.Neighbourhood)
    return result.Neighbourhood

def getperiod(x):
    if x=='0':
        period='Night'
    elif x=='6':
        period='Morning'
    elif x=='12':
        period='Afternoon'
    else:
        period='Evening'
    return period

def getrisk(x):
    if x <= 33:
        risk='Low'
    elif x > 33 and x <= 66:
        risk='Medium'
    else:
        risk='High'
    return risk

def loaded_model(model):
    #loding model 
    # load json and create model
    json_file = open('/'+model+'_structure.json', 'r')
    loaded_model_json = json_file.read()
    json_file.close()
    loaded_model = model_from_json(loaded_model_json)
    # load weights into new model
    loaded_model.load_weights('/'+model+'_weights.h5')
    print("Loaded model from disk")
    
    return loaded_model

def point_inside_polygon(y,x,poly):

    n = len(poly)
    inside =False

    p1x,p1y = poly[0]
    for i in range(n+1):
        p2x,p2y = poly[i % n]
        if y > min(p1y,p2y):
            if y <= max(p1y,p2y):
                if x <= max(p1x,p2x):
                    if p1y != p2y:
                        xinters = (y-p1y)*(p2x-p1x)/(p2y-p1y)+p1x
                    if p1x == p2x or x <= xinters:
                        inside = not inside
        p1x,p1y = p2x,p2y

    return inside

def coordinate_to_neighbourhood(lat,lon,neigReverseID, city_geojson):
    flag=-1
    for index in range(1,141):
        if(point_inside_polygon(lat, lon, city_geojson.features[index-1]["geometry"]["coordinates"][0] )):
            topoMapID= index
    return neigReverseID["values"][topoMapID-1]["reverse"]


if __name__ == '__main__':
    loaded_model = loaded_model("crimes_hours_model")
    NBList = pd.read_json('/Neighbourhoods.csv', orient='records')
    neigReverseID = pd.read_json('/neighbours_reverse.json')
    city_geojson = pd.read_json('/toronto_geojson.json')
    app.run(threaded=False, port=5000, host='0.0.0.0')
    
