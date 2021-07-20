# -*- coding: utf-8 -*-

import pandas as pd
import requests
import json
import numpy as np
from math import radians, sin, cos, acos
from pandas.io.json import json_normalize


class GoogleGeocodin(object):
    def __init__(self, apiKey):
        super(GoogleGeocodin, self).__init__()
        self.apiKey = apiKey

    def search_places_by_coordinate(self, pincode,district,city,state):
      #fetches the lat and long coordinates of a given pincode
      #Uses the pincodes and the district,city,state related to the pincode to get the data.
        endpoint_url = "https://maps.googleapis.com/maps/api/geocode/json?"
        params = {
            'key': self.apiKey,
            'address': pincode+district+city+state}
        res = requests.get(endpoint_url, params = params)
        result =  json.loads(res.content)
        data = pd.json_normalize(result["results"])
        return data

    def distance_by(self,costomer_state,costomer_city,costomer_district,state,city,district):
      #calculates the driving distance between two given cities.
        endpoint_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        params = {
            "key":self.apiKey,
            "origins":costomer_city+costomer_district+costomer_state,
            "destinations":city+district+state }
        res1 = requests.get(endpoint_url, params = params)
        result1 =  json.loads(res1.content)
        data1 = pd.json_normalize(result1["rows"])
        return data1

def min_distance(costomer_pincode, api_key):
  #Calculates the minimum distance to the costsomer's address pincode from the cities we work or have worked in.
  #First we get the data respective to the costomer's pincode
  #Next we compare the distance between costomer's pincode to all the pincodes we work in.
  #Finally we get the minimum distance in output, it is 0 if we work in the given pincode.
  df1 = pd.read_excel ('city_in_last_6_months.xlsx')
  df1 = df1.sort_values(by = "city in last 6 months" , ascending = False).reset_index().drop(["index"],1)

  a = GoogleGeocodin(api_key)
  data = df1[df1["Pincode"] == int(costomer_pincode)].reset_index()
  if data["city in last 6 months"][0] == 'yes':
    return "0 km"
  costomer_city = data["City/ Locality name"][0]
  costomer_state = data["State"][0]
  costomer_district = data["District"][0]
  i = 0
  dist = []
  error_cities=[]
  df2 = df1.drop_duplicates(subset ="City/ Locality name", keep = "first").reset_index()
  # print(len(df2["city in last 6 months"]))
  while (df2["city in last 6 months"][i] == 'yes'):
    city = df2["City/ Locality name"][i]
    state = df2["State"][i]
    district = df2["District"][i]
    if costomer_state == state:
      try2 = a.distance_by(costomer_state,costomer_city,costomer_district,state,city,district)
      if try2["elements"][0][0].get("status") != "OK":
        error_cities.append(df2["City/ Locality name"][i])
        i+=1
        continue
      dist.append((try2["elements"][0][0].get("distance").get("value"))/1000)
    i+=1
    print(i)

  if dist:
    return str(min(dist))+" km"
  else:
    return "customer's state not served"

def get_token():
  #gets the token value for the api to extract data
  Url = "https://devapi.letsmd.com/oauth/token"

  payload = 'client_id=7&grant_type=client_credentials&client_secret=up5VwUreS5kwr6eF00eRyk3YcOwdCq9BozwJB8GR&scope=*'
  headers = {
  'Content-Type': 'application/x-www-form-urlencoded',
  'Cookie': '__cfduid=d31baa725f14bdea78cd02f95b8b32eb71594296309'
    }

  response = requests.request("POST", Url, headers=headers, data = payload)
  a =response.text
  a = a[1:]
  token = eval(a)
  return token.get("access_token")

def fetch(token, lead_id):
  #fetches data from the api from credit leads
  url = "https://devapi.letsmd.com/v1/loan-lead/get-kyc-info/pancard/" + str(lead_id)
  payload = {}
  headers = {
  'Authorization': 'Bearer '+ token,
  'Cookie': '__cfduid=d31baa725f14bdea78cd02f95b8b32eb71594296309'
      }

  response = requests.request("GET", url, headers=headers, data = payload)
  b =response.text
  b = b[1:]

  pincode = eval(b).get("data",{})
  if "c_address_pincode" in pincode:
    return pincode.get("c_address_pincode",{})
  else:
    return 0


def main(lead_pincode, api_key):

  #costomer's adderess pincode to calculate the distance
  pincode = fetch(get_token(), lead_pincode)

  #Driver call to get the result
  if 100000 <= pincode <= 999999:
    return min_distance(pincode, api_key)
  else:
    return "NA"

