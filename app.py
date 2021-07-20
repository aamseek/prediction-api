from flask import Flask, jsonify, request
from flask_pymongo import PyMongo
import pandas as pd
import math
import json
import urllib
import income_prediction
import final_pincode
import EPFO_Scraper
import os
from config import *


# app
app = Flask(__name__)

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "client_secrets.json"

# app.config['MONGO_URI'] = 'mongodb://127.0.0.1:27017/letsmd'

app.config.from_pyfile('config.py')

mongo = PyMongo(app)

@app.route('/api/v1/pincode_distance/', methods=['POST'])
def pincode_distance():
    data = request.get_json(force=True)
    lead_id = data['lead_id']
    resp = {}
    resp["distance"] = final_pincode.main(lead_id, API_KEY)
    response = {
        "statusCode": 200,
        "data": resp
    }
    return response

@app.route('/api/v1/company_details/', methods=['POST'])
def company_details():
    data = request.get_json(force=True)
    lead_id = data['lead_id']

    leads = mongo.db.leads
    result = leads.find_one({'lead_id':lead_id}, projection = {'_id':0,'borrower.work.company_name':1})

    if result:
        company = result.get('borrower', {}).get('work',{}).get('company_name',{})
    else:
        company = None

    dict1 = {'input':company, 'key':API_KEY}
    qstr = urllib.parse.urlencode(dict1)
    URL = 'https://maps.googleapis.com/maps/api/place/findplacefromtext/json?inputtype=textquery&fields=formatted_address,name,business_status,rating,user_ratings_total,types,geometry&'
    URL = URL + qstr
    response = urllib.request.urlopen(URL)
    data = json.load(response)
    if data['candidates']:
        address = data['candidates'][0]['formatted_address']
        name = data['candidates'][0]['name']
        business_status = data['candidates'][0]['business_status']
        rating = data['candidates'][0]['rating']
        user_ratings_total = data['candidates'][0]['user_ratings_total']
        types = data['candidates'][0]['types']
        geometry = data['candidates'][0]['geometry']['location']
    else:
        address = None
        name = None
        business_status = None
        rating = None
        user_ratings_total = None
        types = None
        geometry = None

    resp = {}
    resp["address"] = address
    resp["name"] = name
    resp["business_status"] = business_status
    resp["rating"] = rating
    resp["user_ratings_total"] = user_ratings_total
    resp["types"] = types
    resp["geometry"] = geometry

    status_code = 200
    response = {
        "statusCode": status_code,
        "data": resp
    }

    return response


@app.route('/api/v1/income/', methods=['POST'])
def predict():

    data = request.get_json(force=True)
    lead_id = data['lead_id']

    leads = mongo.db.leads
    result = leads.find_one({'lead_id':lead_id}, projection = {'_id':0,'borrower.lenderApprovalObject.dmi.readyForDecisionResponse.multibureauData.FINISHED.JSON-RESPONSE-OBJECT':1,'borrower.dob':1,'borrower.gender':1,'borrower.work.employment_type':1})

    response_data = income_prediction.main(result)
    return response_data

@app.route('/epfo/', methods=['GET'])
def org_search_details():
    org_name = request.args.get('org_name', "")
    f_emp_name = request.args.get('f_emp_name', "")
    l_emp_name = request.args.get('l_emp_name', "")
    org_code = request.args.get('code', "0")

    result = "Invalid Captcha"
    counter = 0
    while result == "Invalid Captcha" and counter < 5:
        result = EPFO_Scraper.main(org_name, f_emp_name, l_emp_name, org_code)
        counter += 1
    if result == "Invalid Captcha":
        return {"data": ["Invalid Captcha"], "status_code":503, "status":"fail"}
    else:
        return result

if __name__ == '__main__':
    app.run(host = '0.0.0.0')
