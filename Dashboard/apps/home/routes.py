# -*- encoding: utf-8 -*-
"""
Copyright (c) 2019 - present AppSeed.us
"""

from apps.home import blueprint
from flask import render_template, request
from flask_login import login_required
from jinja2 import TemplateNotFound

import requests

SB_URL = "http://127.0.0.1:5050/" #http://172.17.0.1:5000/

def getDataFromCSB(url):
    return requests.post(url) 
    

@blueprint.route('/index')
#@login_required
def index():
    context = {"test": "test", "csp": "Not connected"}
    try:
        reply = requests.get(SB_URL + "status")
        data = reply.json()
        print("Code: " + str(reply.status_code))     
        if reply.status_code == 200: 
            context["connected_devices"] = len(data["connected_devices"])
            context["csp"] = "Connected"
            context["log"] = data["log"]

            if "DPS HV" in data["asset_discovery"]: 
                context["AD_DPSHV"] = data["asset_discovery"]["DPS HV"]                

            if "DPS RS" in data["asset_discovery"]: 
                context["AD_DPSRS"] = data["asset_discovery"]["DPS RS"]

            if "DPS MV" in data["asset_discovery"]: 
                context["AD_DPSMV"] = data["asset_discovery"]["DPS MV"]                

            if "DSS2 GW" in data["asset_discovery"]: 
                context["AD_DSS2GW"] = data["asset_discovery"]["DSS2 GW"]                

            context["asset_discovery"] = data["asset_discovery"]

            #print(data["asset_discovery"])
        else:
            context["connected_devices"] = 0
    except requests.RequestException as e:
        #raise SystemError(e)
        print("Error in connection " + str(e))

    return render_template('home/index.html', segment='index', **context)


@blueprint.route('/<template>')
#@login_required
def route_template(template):

    try:
        context = {"connected_devices" : 6, 
                   "csp" : "Not connected"}
        #data['connected_devices'] = 6

        if not template.endswith('.html'):
            template += '.html'

        # Detect the current page
        segment = get_segment(request)

        # Serve the file (if exists) from app/templates/home/FILE.html
        return render_template("home/" + template, segment=segment, **context)

    except TemplateNotFound:
        return render_template('home/page-404.html'), 404

    except:
        return render_template('home/page-500.html'), 500


# Helper - Extract current page name from request
def get_segment(request):

    try:

        segment = request.path.split('/')[-1]

        if segment == '':
            segment = 'index'

        return segment

    except:
        return None
