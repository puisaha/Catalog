from flask import (
                    Flask,
                    render_template,
                    request,
                    redirect,
                    jsonify,
                    url_for,
                    flash)

from sqlalchemy import create_engine, asc
from sqlalchemy.orm import sessionmaker
from database_setup import Base, Shop, DressItem, User

from flask import session as login_session
import random
import string

from oauth2client.client import flow_from_clientsecrets
from oauth2client.client import FlowExchangeError
import httplib2
import json
from flask import make_response
import requests

app = Flask(__name__)

CLIENT_ID = json.loads(
    open('client_secrets.json', 'r').read())['web']['client_id']
APPLICATION_NAME = "Catalog Application"


# Connect to Database and create database session
engine = create_engine('sqlite:///shopitems.db')
Base.metadata.bind = engine

DBSession = sessionmaker(bind=engine)
session = DBSession()


# Create anti-forgery state token
@app.route('/login')
def showLogin():
    state = ''.join(random.choice(string.ascii_uppercase + string.digits)
                    for x in xrange(32))
    login_session['state'] = state
    # return "The current session state is %s" % login_session['state']
    return render_template('login.html', STATE=state)


@app.route('/gconnect', methods=['POST'])
def gconnect():
    """
    Gathers data from Google Sign In API and places it inside a
    session variable.
    """
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
    print "2###"
    # If there was an error in the access token info, abort.
    if result.get('error') is not None:
        response = make_response(json.dumps(result.get('error')), 500)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is used for the intended user.
    gplus_id = credentials.id_token['sub']
    print "3###"
    if result['user_id'] != gplus_id:
        response = make_response(
            json.dumps("Token's user ID doesn't match given user ID."), 401)
        response.headers['Content-Type'] = 'application/json'
        return response

    # Verify that the access token is valid for this app.
    if result['issued_to'] != CLIENT_ID:
        response = make_response(
            json.dumps("Token's client ID does not match app's."), 401)
        print "Token's client ID does not match app's."
        response.headers['Content-Type'] = 'application/json'
        return response

    stored_access_token = login_session.get('access_token')
    stored_gplus_id = login_session.get('gplus_id')
    print "4###"


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

    print login_session['username']

    # see if user exists, if it doesn't make a new
    user_id = getUserID(login_session['email'])
    if not user_id:
        user_id = createUser(login_session)
    login_session['user_id'] = user_id

    # See if a user exists, if it doesn't make a new one

    output = ''
    output += '<h1>Welcome, '
    output += login_session['username']
    output += '!</h1>'
    output += '<img src="'
    output += login_session['picture']
    output += ' " style = "width: 300px; height:300px; border-radius:150px;'
    output += '-webkit-border-radius: 150px;-moz-border-radius: 150px;"> '
    flash("you are now logged in as %s" % login_session['username'])
    print "done!"
    print login_session['username']
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
        # Only disconnect a connected user.
    access_token = login_session.get('access_token')
    if access_token is None:
        response = make_response(
            json.dumps('Current user not connected.'), 401)
        response.headers['Content-Type'] = 'application/json'
        return response
    url = 'https://accounts.google.com/o/oauth2/revoke?token=%s' % access_token
    h = httplib2.Http()
    result = h.request(url, 'GET')[0]

    if result['status'] == '200':
        # Reset the user's sesson.
        del login_session['access_token']
        del login_session['gplus_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']

        response = make_response(json.dumps('Successfully disconnected.'), 200)
        response.headers['Content-Type'] = 'application/json'
        return response
    else:
        # For whatever reason, the given token was invalid.
        response = make_response(
            json.dumps('Failed to revoke token for given user.', 400))
        response.headers['Content-Type'] = 'application/json'
        return response


# JSON APIs to view Restaurant Information
@app.route('/shop/<int:shop_id>/item/JSON')
def shopMenuJSON(shop_id):
    shop = session.query(Shop).filter_by(id=shop_id).one()
    items = session.query(DressItem).filter_by(
        shop_id=shop_id).all()
    return jsonify(MenuItems=[i.serialize for i in items])


@app.route('/shop/<int:shop_id>/item/<int:item_id>/JSON')
def menuItemJSON(shop_id, item_id):
    Dress_Item = session.query(DressItem).filter_by(id=item_id).one()
    return jsonify(Dress_Item=Dress_Item.serialize)


@app.route('/shop/JSON')
def shopssJSON():
    shops = session.query(Shop).all()
    return jsonify(shops=[r.serialize for r in shops])


# Show all shops
@app.route('/')
@app.route('/shop/')
def showShops():
    shops = session.query(Shop).order_by(asc(Shop.name))

    if 'username' not in login_session:  # make sure user has logined
        return render_template(
            'publiccatalog.html', shop=shops, creator='Amrita')
    else:  # if user logined, able to access create a new item
        return render_template('shops.html', shops=shops)
# Create a new restaurant


@app.route('/shop/new/', methods=['GET', 'POST'])
def newShop():
    if 'username' not in login_session:
        return redirect('/login')
    if request.method == 'POST':
        newShop = Shop(
            name=request.form['name'], creator_id=login_session['user_id'])
        session.add(newShop)
        flash('New Shop %s Successfully Created' % newShop.name)
        session.commit()
        return redirect(url_for('showShops'))
    else:
        return render_template('newShop.html')

# Edit a shop


@app.route('/shop/<int:shop_id>/edit/', methods=['GET', 'POST'])
def editShop(shop_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedShop = session.query(
        Shop).filter_by(id=shop_id).one()
    if editedShop.creator_id == login_session['user_id']:
        if request.method == 'POST':
            if request.form['name']:
                editedShop.name = request.form['name']
                flash('Shop Successfully Edited %s' % editedShop.name)
                return redirect(url_for('showShops'))
        else:
            return render_template('editShop.html', shop=editedShop)
    else:
        return redirect(url_for('showShops'))


# Delete a shop
@app.route('/shop/<int:shop_id>/delete/', methods=['GET', 'POST'])
def deleteShop(shop_id):
    if 'username' not in login_session:
        return redirect('/login')
    shopToDelete = session.query(
        Shop).filter_by(id=shop_id).one()
    if shopToDelete.creator_id == login_session['user_id']:
        if request.method == 'POST':
            session.delete(shopToDelete)
            flash('%s Successfully Deleted' % shopToDelete.name)
            session.commit()
            return redirect(url_for('showShops'))
        else:
            return render_template('deleteShop.html', shop=shopToDelete)
    else:
        return redirect(url_for('showShops'))


# Show a restaurant menu


@app.route('/shop/<int:shop_id>/')
@app.route('/shop/<int:shop_id>/item/')
def showItem(shop_id):
    shop = session.query(Shop).filter_by(id=shop_id).one()
    items = session.query(DressItem).filter_by(
        shop_id=shop_id).all()
    return render_template(
        'item.html', items=items, shop=shop,
        user=login_session['username'], pic=login_session['picture'])


# Create a new  item
@app.route('/shop/<int:shop_id>/item/new/', methods=['GET', 'POST'])
def newDressItem(shop_id):
    if 'username' not in login_session:
        return redirect('/login')
    shop = session.query(Shop).filter_by(id=shop_id).one()
    if request.method == 'POST':
        newItem = DressItem(
            name=request.form.get('name', None),
            description=request.form.get('description', None),
            price=request.form.get('price', None),
            course=request.form.get('course', None),
            shop_id=shop_id, creator_id=login_session['user_id'])
        session.add(newItem)
        session.commit()
        flash('New Dress %s Item Successfully Created' % (newItem.name))
        return redirect(url_for('showItem', shop_id=shop_id))
    else:
        return render_template('newdressitem.html', shop_id=shop_id)

# Edit a menu item


@app.route(
    '/shop/<int:shop_id>/item/<int:item_id>/edit', methods=['GET', 'POST'])
def editItem(shop_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    editedItem = session.query(DressItem).filter_by(id=item_id).one()
    if editedItem.creator_id == login_session['user_id']:
        shop = session.query(Shop).filter_by(id=shop_id).one()
        if request.method == 'POST':
            if request.form.get('name', None):
                editedItem.name = request.form.get('name', None)
            if request.form.get('description', None):
                editedItem.description = request.form.get('description', None)
            if request.form.get('price', None):
                editedItem.price = request.form.get('price', None)
            if request.form.get('course', None):
                editedItem.course = request.form.get('course', None)
            session.add(editedItem)
            session.commit()
            flash('Dress Item Successfully Edited')
            return redirect(url_for('showItem', shop_id=shop_id))
        else:
            return render_template(
                'editdressitem.html', shop_id=shop_id,
                item_id=item_id, item=editedItem)
    else:
        return redirect(url_for('showItem', shop_id=shop_id))


# Delete a menu item
@app.route(
    '/shop/<int:shop_id>/item/<int:item_id>/delete', methods=['GET', 'POST'])
def deleteItem(shop_id, item_id):
    if 'username' not in login_session:
        return redirect('/login')
    itemToDelete = session.query(DressItem).filter_by(id=item_id).one()
    if itemToDelete.creator_id == login_session['user_id']:
        shop = session.query(Shop).filter_by(id=shop_id).one()
        if request.method == 'POST':
            session.delete(itemToDelete)
            session.commit()
            flash('Dress Item Successfully Deleted')
            return redirect(url_for('showItem', shop_id=shop_id))
        else:
            return render_template('deleteDressItem.html', item=itemToDelete)
    else:
        return redirect(url_for('showItem', shop_id=shop_id))
# Disconnect based on provider


@app.route('/disconnect')
def disconnect():
    if 'provider' in login_session:
        if login_session['provider'] == 'google':
            gdisconnect()
            del login_session['gplus_id']
            del login_session['access_token']
        if login_session['provider'] == 'facebook':
            fbdisconnect()
            del login_session['facebook_id']
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        del login_session['provider']
        flash("You have successfully been logged out.")
        return redirect(url_for('showShops'))
    elif 'username' in login_session:
        del login_session['username']
        del login_session['email']
        del login_session['picture']
        del login_session['user_id']
        flash("You have successfully been logged out.")
        return redirect(url_for('showShops'))
    else:
        flash("You were not logged in")
        return redirect(url_for('showShops'))


if __name__ == '__main__':
    app.secret_key = 'super_secret_key'
    app.debug = True
    app.run(host='0.0.0.0', port=5000)
