from flask import Flask, render_template, request, redirect
from flask import jsonify, url_for, flash, g
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Activity, Legend, User
from flask import session as login_session
import random
import string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests
from functools import wraps

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if ('username' not in login_session):
            flash("You need to login to access that feature")
            return redirect(url_for('showLogin'))
        return f(*args, **kwargs)
    return decorated_function


# Connect to Database and create database session
engine = create_engine('sqlite:///gr8est.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()

# Create anti-forgery state token


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in range(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    # Validate state token
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    # Obtain authorization code
    code = request.data

    try:
        # Upgrade the authorization code into a credentials object
        oauth_flow = flow_from_clientsecrets('client_secrets.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(
            json.dumps('Failed to upgrade the authorization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Check that the access token is valid.
    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print ("Token's client ID does not match app's.")
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_access_token is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('User is already connected.'),
                                 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Store the access token in the session for later use.
    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # Get user info
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email'] = data['email']
    # ADD PROVIDER TO LOGIN SESSION
    login_session['provider'] = 'google'

    # see if user exists, if it doesn't make a new one
    user_id = getUserID(data["email"])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    flash("you are now logged in as %s" % login_session['username'])
    print ("done!")
    return output

# User Helper Functions


def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email=login_session['email']).one()
    return user.id


def getUserInfo(user_id):
    user = session.query(User).filter_by(id=user_id).one()
    return user


def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

# DISCONNECT - Revoke a current user's token and reset their login_session


@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session.get('access_token')
    if access_token is None:
        print ('Access Token is None')
        response = make_response(json.dumps('User not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    print ('In gdisconnect access token is %s' % access_token)
    print ('User name is: ')
    print (login_session['username'])
    requests.post('https://accounts.google.com/o/oauth2/revoke',
                  params={'token': access_token},
                  headers={'content-type': 'application/json'})
    del login_session['access_token']
    del login_session['gplus_id']
    del login_session['username']
    del login_session['email']
    del login_session['picture']
    return redirect(url_for('showActivities'))


# JSON APIs to view activity Information


@app.route('/activity/<int:activity_id>/legend/JSON')
def activityLegendJSON(activity_id):
    activity = session.query(Activity).filter_by(id=activity_id).one()
    legends = session.query(Legend).filter_by(activity_id=activity_id).all()
    return jsonify(legends=[i.serialize for i in legends])


@app.route('/activity/<int:activity_id>/legend/<int:legend_id>/JSON')
def legendJSON(activity_id, legend_id):
    legend = session.query(Legend).filter_by(id=legend_id).one()
    return jsonify(legend=legend.serialize)


@app.route('/activity/JSON')
def activityJSON():
    activity = session.query(Activity).all()
    return jsonify(activity=[r.serialize for r in activity])


# Show all activities


@app.route('/')
@app.route('/activity/')
def showActivities():
    activities = session.query(Activity).order_by(asc(Activity.name))
    if 'username' not in login_session:
        return render_template('publicactivity.html', activity=activities)
    else:
        return render_template('activities.html', activity=activities)

# Create a new activity


@app.route('/activity/new/', methods=['GET', 'POST'])
@login_required
def newActivity():
        if request.method == 'POST':
            newactivity = Activity(name=request.form['name'])
            session.add(newactivity)
            flash('New activity %s Successfully Created' % newactivity.name)
            session.commit()
            return redirect(url_for('showActivities'))
        else:
            return render_template('newactivity.html')

# Edit an activity


@app.route('/activity/<int:activity_id>/edit/', methods=['GET', 'POST'])
@login_required
def editActivity(activity_id):
    activities = session.query(Activity).order_by(asc(Activity.name))
    editedactivity = session.query(Activity).filter_by(id=activity_id).one()
    creator = getUserInfo(Activity.user_id)
    if ('username' not in login_session or
        creator.id != login_session['user_id']):
            flash("You do not have access to make that change")
            return render_template('publicactivity.html', activity=activities)
    else:
        if request.method == 'POST':
            if request.form['name']:
                editedactivity.name = request.form['name']
                flash('activity Successfully Edited %s' % editedactivity.name)
                return redirect(url_for('showActivities'))
        else:
            return render_template('editactivity.html',
                                   activity=editedactivity)


# Delete an activity


@app.route('/activity/<int:activity_id>/delete/', methods=['GET', 'POST'])
@login_required
def deleteActivity(activity_id):
    activities = session.query(Activity).order_by(asc(Activity.name))
    activityToDelete = session.query(Activity).filter_by(id=activity_id).one()
    creator = getUserInfo(Activity.user_id)
    if ('username' not in login_session or
        creator.id != login_session['user_id']):
            flash("You do not have access to make that change")
            return render_template('publicactivity.html', activity=activities)
    else:
        if request.method == 'POST':
            session.delete(activityToDelete)
            flash('%s Successfully Deleted' % activityToDelete.name)
            session.commit()
            return redirect(url_for('showActivities'))
        else:
            return render_template('deleteactivity.html',
                                   activityToDelete=activityToDelete,
                                   activity_id=activity_id)

# Show an activity legend list


@app.route('/activity/<int:activity_id>/')
@app.route('/activity/<int:activity_id>/legend/')
def showLegend(activity_id):
    activity = session.query(Activity).filter_by(id=activity_id).one()
    legends = session.query(Legend).filter_by(activity_id=activity_id).all()
    creator = getUserInfo(Activity.user_id)

    if ('username' not in login_session or
        creator.id != login_session['user_id']):
            return render_template('publiclegend.html',
                                   legends=legends, activity=activity)
    else:
        return render_template('legend.html', legends=legends,
                               activity=activity, creator=creator)

# Create a new legend


@app.route('/activity/<int:activity_id>/legend/new/', methods=['GET', 'POST'])
@login_required
def newLegend(activity_id):
    activity = session.query(Activity).filter_by(id=activity_id).one()
    if request.method == 'POST':
        newItem = Legend(name=request.form['name'],
                         description=request.form['description'],
                         salary=request.form['salary'],
                         stats=request.form['stats'],
                         activity_id=activity_id)
        session.add(newItem)
        session.commit()
        flash('New legend %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showLegend', activity_id=activity_id))
    else:
        return render_template('newlegend.html', activity_id=activity_id)

# Edit a legend item


@app.route('/activity/<int:activity_id>/legend/<int:legend_id>/edit',
           methods=['GET', 'POST'])
@login_required
def editLegend(activity_id, legend_id):
    activities = session.query(Activity).order_by(asc(Activity.name))
    editedLegend = session.query(Legend).filter_by(id=legend_id).one()
    activity = session.query(Activity).filter_by(id=activity_id).one()
    creator = getUserInfo(Legend.user_id)
    if ('username' not in login_session or
        creator.id != login_session['user_id']):
            flash("You do not have access to make that change")
            return render_template('publicactivity.html', activity=activities)
    else:
        if request.method == 'POST':
            if request.form['name']:
                editedLegend.name = request.form['name']
            if request.form['description']:
                editedLegend.description = request.form['description']
            if request.form['salary']:
                editedLegend.salary = request.form['salary']
            if request.form['stats']:
                editedLegend.stats = request.form['stats']
            session.add(editedLegend)
            session.commit()
            flash('Legend Successfully Edited')
            return redirect(url_for('showLegend', activity_id=activity_id))
        else:
            return render_template('editlegend.html', activity_id=activity_id,
                                   legend_id=legend_id, legend=editedLegend)


# Delete a legend


@app.route('/activity/<int:activity_id>/legend/<int:legend_id>/delete',
           methods=['GET', 'POST'])
@login_required
def deleteLegend(activity_id, legend_id):
    activities = session.query(Activity).order_by(asc(Activity.name))
    activity = session.query(Activity).filter_by(id=activity_id).one()
    legendToDelete = session.query(Legend).filter_by(id=legend_id).one()
    creator = getUserInfo(Legend.user_id)
    if ('username' not in login_session or
        creator.id != login_session['user_id']):
            flash("You do not have access to make that change")
            return render_template('publicactivity.html', activity=activities)
    else:
        if request.method == 'POST':
            session.delete(legendToDelete)
            session.commit()
            flash('Legend Item Successfully Deleted')
            return redirect(url_for('showLegend', activity_id=activity_id))
        else:
            return render_template('deletelegend.html', legend=legendToDelete,
                                   activity_id=activity_id,
                                   legend_id=legend_id)

if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=8000)
