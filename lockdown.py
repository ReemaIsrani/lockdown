
from cloudant import Cloudant
from flask import Flask, render_template, request, jsonify
import atexit
import os
import json
from flask import Flask, request, jsonify
import joblib
from datetime import timedelta
import traceback
import pandas as pd
import numpy as np
import requests
from datetime import datetime
import pickle
import base64

app = Flask(__name__)
port = int(os.getenv('PORT', 8000))

@app.route('/lockdown', methods=['POST','GET'])
def lockdown():
    try:
        today=datetime.today().strftime('%d-%m-%Y')
        s_date=datetime.strptime('01-07-2020','%d-%m-%Y')
        e_date=datetime.strptime(today,'%d-%m-%Y')
        dates=pd.date_range(s_date,e_date,freq='d')
        case_dates=[]
        for d in dates:
            d1 = d - timedelta(days=2)
            d2=d1.strftime('%d-%m-%Y')
            case_dates.append(d2)
        x= requests.get('https://api.covid19india.org/data.json')
        data_stats = x.json()
        data = data_stats["cases_time_series"]
        confirmed=[]
        active=[]
        death=[]
        recovered=[]
        date=[]
        print(case_dates)
        for i in data:
            confirmed.append(i["dailyconfirmed"])
            death.append(i["dailydeceased"])
            recovered.append(i["dailyrecovered"])
            date.append(i["date"])
            activee=int(i["dailyconfirmed"])-(int(i["dailydeceased"])+int(i["dailyrecovered"]))
            active.append(activee)
        cases=pd.DataFrame()
        cases['date']=date
        cases['confirmed']=confirmed
        cases['active']=active
        cases['death']=death
        cases['recovered']=recovered

        cdates=[]
        for d in cases['date']:
            d1=d.strip()+' 2020'
            d2=datetime.strptime(d1,'%d %B %Y').strftime('%d-%m-%Y')
            cdates.append(d2)
        cases['date']=cdates
        cases1=cases[cases['date'].isin(case_dates)]
        scaler=joblib.load('scaler.save')
        gbr=joblib.load('gbr.sav')
        #x=scaler.transform(cases1.iloc[:,[1,2,3]])
        y=gbr.predict(cases1.iloc[:,[1,2,3]])
        output=pd.DataFrame()
        output['case_date']=cases1['date']
        output['confirmed']=cases1['confirmed']
        output['active']=cases1['active']
        output['death']=cases1['death']
        output['recovered']=cases1['recovered']
        output['sentiment_date']=dates
        output['sentiment_score']=y
        output=output.reset_index(drop=True)
        print(output)
        pickled = pickle.dumps(output)
        pickled_b64 = base64.b64encode(pickled)
        hug_pickled_str = pickled_b64.decode('utf-8')
        return jsonify({'prediction': hug_pickled_str})
        
    except:
        return jsonify({'trace': traceback.format_exc()})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=port, debug=True)
