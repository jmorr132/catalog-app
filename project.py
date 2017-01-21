from flask import Flask, render_template, request, redirect, jsonify, url_for, flash
from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Item, User
from flask import session as login_session
import random, string
from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app =Flask(__name__)
CLIENT_ID = json.loads(
    open('client_secret.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Trash_Into_Cash"

engine = create_engine('sqlite:///items.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                   for x in xrange(32))
    login_session['state'] = state
    return render_template('login.html', STATE=state)

@app.route('/gconnect', methods=["POST"])
def gconnect():
    if request.args.get('state') != login_session['state']:
       response = make_response(json.dumps('Invalid state parameter.'), 401)
       response.headers['Content-Type'] = 'application/json'
       return response
    code = request.data

    try:
        oauth_flow = flow_from_clientsecrets('client_secret.json', scope='')
        oauth_flow.redirect_uri = 'postmessage'
        credentials = oauth_flow.step2_exchange(code)
    except FlowExchangeError:
        response = make_response(json.dumps('Failed to upgrade the authroization code.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    access_token = credentials.access_token
    url = ('https://www.googleapis.com/oauth2/v1/tokeninfo?access_token=%s'
           % access_token)
    h = httplib2.Http()
    result = json.loads(h.request(url, 'GET')[1])
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] ='application/json'
        return response
    
    gplus_id = credentials.id_token['sub']
    if result['user_id'] != gplus_id:
        response = make_response(json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    
    if result['issued_to'] != CLIENT_ID:
        response = make_response(json.dumps("Tokens Client ID does not match apps"), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_credentials = login_session.get('credentials')
    stored_gplus_id = login_session.get('gplus_id')
    if stored_credentials is not None and gplus_id == stored_gplus_id:
        response = make_response(json.dumps('current user is already connected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response

    login_session['access_token'] = credentials.access_token
    login_session['gplus_id'] = gplus_id

    # this gets user info from googleapis
    userinfo_url = "https://www.googleapis.com/oauth2/v1/userinfo"
    params = {'access_token': credentials.access_token, 'alt': 'json'}
    answer = requests.get(userinfo_url, params=params)

    data = answer.json()

    login_session['username'] = data['name']
    login_session['picture'] = data['picture']
    login_session['email']= data['email']
    login_session['provider'] = 'google'

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id']= user_id


    output = ''
    output += '<h1> Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    return output

def createUser(login_session):
    newUser = User(name=login_session['username'], email=login_session[
                   'email'], picture=login_session['picture'])
    session.add(newUser)
    session.commit()
    user = session.query(User).filter_by(email = login_session['email']).one()
    return user.id

def getUserID(email):
    try:
        user = session.query(User).filter_by(email=email).one()
        return user.id
    except:
        return None

def getUserInfo(user_id):
    user = session.query(User).filter_by(id = user_id).one()
    return user

@app.route('/gdisconnect')
def gdisconnect():
    access_token = login_session['access_token']
    if access_token is None:
        response = make_response(json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % login_session['access_token']
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]
    if result['status'] != '200':    
        response = make_response(json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response  

#Facebook connection
@app.route('/fbconnect', methods=['POST'])
def fbconnect():
    if request.args.get('state') != login_session['state']:
        response = make_response(json.dumps('Invalid state parameter.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    access_token = request.data
    print "access token received %s " % access_token

    app_id = json.loads(open('fb_client_secrets.json', 'r').read())[
        'web']['app_id']
    app_secret = json.loads(
        open('fb_client_secrets.json', 'r').read())['web']['app_secret']
    url = ('https://graph.facebook.com/oauth/access_token?grant_type=fb_exchange_token&client_id=%s&client_secret=%s&fb_exchange_token=%s' % (app_id, app_secret, access_token))
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    userinfo_url = "https://graph.facebook.com/v2.4/me"
    token = result.split("&")[0]

    url = 'https://graph.facebook.com/v2.4/me?%s&fields=name,id,email' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]

    data = json.loads(result)

    login_session['provider'] = 'facebook'
    login_session['username'] = data["name"]
    login_session['email'] = data["email"]
    login_session['facebook_id'] = data["id"]

    stored_token = token.split("=")[1]
    login_session['access_token'] = stored_token

    url = 'https://graph.facebook.com/v2.4/me/picture?%s&redirect=0&height=200&width=200' % token
    h = httplib2.Http()
    result = h.request(url, 'GET')[1]
    data = json.loads(result)
    login_session['picture'] = data['data']['url']

    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id
    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height: 300px;border-radius: 150px;-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("Now logged in as %s" % login_session['username'])
    return output

@app.route('/fbdisconnect')
def fbdisconnect():
    facebook_id = login_session['facebook_id']
    access_token = login_session['access_token']
    url = 'https://graph.facebook.com/%s/permissions?access_token=%s' % (facebook_id,access_token)
    h = httplib2.Http()
    result = h.request(url, 'DELETE')[1]
    return "you have been logged out"

# Disconnect based on provider
@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showItems'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showItems'))

@app.route('/item/<int:item_id>/itemdetail/JSON')
def itemDetailJSON(item_id):
    item = session.query(Item).filter_by(id=item_id).all()
    return jsonify(Item=[i.serialize for i in item])

@app.route('/item/<int:item_id>/itemdetail/<int:detail_id>/JSON')
def itemDetailsJSON(item_id, detail_id):
    item_detail= session.query(ItemDetails).filter_by(id=detail_id).one()
    return jsonify(item_detail = item_detail.serialize)

@app.route('/item/JSON')
def itemJSON():
    items = session.query(Item).all()
    return jsonify(items=[i.serialize for i in items])


@app.route('/')
@app.route('/item/')
def showItems():  
    item = session.query(Item).all()
    if 'username' not in login_session:
        return render_template('publicItems.html', item=item,)
    else:
        user = session.query(User).filter_by(picture=login_session['picture']).one()
        return render_template('items.html', item=item, user=user)

@app.route('/item/new', methods = ['GET', 'POST'])
def newItem():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newItem = Item(title=request.form['title'],
                       itemPicture = request.form['picture'],
                       price = request.form['price'],
                       description = request.form['description'],
                       itemtype = request.form['itemtype'],
                       location = request.form['location'],
                       contactinfo = request.form['contactinfo'],
                       user_id = login_session['user_id'])
        flash("%s Successfully Posted for sale!" % newItem.title)
        session.add(newItem)
        session.commit()   
        return redirect(url_for('showItems'))
    else:
        return render_template('newItem.html')

@app.route('/item/<int:item_id>/edit/', methods =['GET', 'POST'])
def editItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        item = session.query(Item).filter_by(id = item_id).one()
        editedItem = session.query(Item).filter_by(id = item_id).one()
        if item.user_id == login_session['user_id']:
            if request.method =='POST':
                if request.form['title']:
                    editedItem.title = request.form['title']
                if request.form['itemPicture']:
                    editedItem.itemPicture = request.form['itemPicture']
                if request.form['price']:
                    editedItem.price = request.form['price']
                if request.form['itemtype']:
                    editedItem.itemtype = request.form['itemtype']
                if request.form['description']:
                    editedItem.description = request.form['description']
                session.add(editedItem)
                session.commit()
                return redirect(url_for('showItems'))
            else:
                return render_template('editItem.html', item = editedItem)
        else:
            flash('Error: You are not the Seller of this Item')
            return redirect(url_for('showItems'))
@app.route('/item/<int:item_id>/delete/', methods = ['GET', 'POST'])
def deleteItem(item_id):
    if 'username' not in login_session:
        return redirect('/login')
    else:
        item = session.query(Item).filter_by(id = item_id).one()
        itemToDelete = session.query(Item).filter_by(id = item_id).one()
        if item.user_id == login_session['user_id']:
            if request.method == 'POST':
                session.delete(itemToDelete)
                session.commit()
                return redirect(url_for('showItems', item_id = item_id))
            else:
                return render_template("deleteItem.html", item = itemToDelete)
        else:
            flash('Error: You are not the Seller of this Item')
            return redirect(url_for('showItems'))
# Show Item Details
@app.route('/item/<int:item_id>')
@app.route('/item/<int:item_id>/itemdetail/')
def showItemDetail(item_id):
    user = session.query(User).filter_by(picture=login_session['picture']).one()
    item = session.query(Item).filter_by(id=item_id).all()
    return  render_template('itemDetail.html', item = item, user=user)


     
if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)

