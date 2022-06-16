from flask import Flask, render_template, request, session, jsonify
import uuid
import pyrebase

# Temporarily replace quote function
def noquote(s):
    return s
  
pyrebase.pyrebase.quote = noquote

app = Flask('app')
app.secret_key = 'super secret string'  # Change this!

firebaseConfig = {
    "apiKey": "AIzaSyAQp7haD6y1dK_7NONoWr2BlCw3hJoyAqY",
    "authDomain": "byte-1e047.firebaseapp.com",
    "projectId": "byte-1e047",
    "storageBucket": "byte-1e047.appspot.com",
    "messagingSenderId": "1024515983734",
    "appId": "1:1024515983734:web:7f60db748ebaf687121257",
    "measurementId": "G-TZ52H98VBN",
    "databaseURL": "https://byte-1e047-default-rtdb.firebaseio.com/"
}

#initialize firebase
firebase = pyrebase.initialize_app(firebaseConfig)
auth = firebase.auth()
db = firebase.database()


# Index
@app.route("/")
def index():
    return render_template('index.html', **locals())
  
# Profile
@app.route("/profile")
def profile():
    return render_template("profile.html", **locals())

# Get User Profile
@app.route("/profiledetails", methods=["POST"])
def profiledetails():
    data = request.get_json()
    try:
        users = db.child("users").order_by_child("address").equal_to(
            data['address']).limit_to_last(1).get()
        for user in users.each():
            data = {"address": user.val()["address"], 
                    "secret": user.val()["secret"], 
                    "email": user.val()["email"]}
    except:
        print('Error in getting profile details'  )
        return jsonify({"success": False, "msg": "Error in getting profile details"})
    print('Profile details gathered.')
    return jsonify({"success": True, "msg": data})
  
# Update Email
@app.route("/updateemail", methods=["POST"])
def updateemail():
    data = request.get_json()
    try:
        users = db.child("users").order_by_child("address").equal_to(
            data['address']).limit_to_last(1).get()
        for user in users.each():
            user_key = user.key()
            user_address = user.val()["address"]
            user_secret = user.val()["secret"]
        data = {"address": user_address, "secret": user_secret, "email": data['email']}
        db.child("users").child(user_key).update(data)
    except:
        print('Error in updating email')
        return jsonify({"success": False, "msg": "Error in updating email"})
    print('Successfully updated the email')
    return jsonify({"success": True, "msg": data})
  
# Regenerate Secret Key
@app.route("/resetsecret", methods=["POST"])
def resetsecret():
    data = request.get_json()
    try:
        secret = uuid.uuid4().hex
        users = db.child("users").order_by_child("address").equal_to(
            data['address']).limit_to_last(1).get()
        for user in users.each():
            user_key = user.key()
        data = {"address": data['address'], "secret": secret}
        db.child("users").child(user_key).update(data)
    except:
        print('Error in reset secret key')
        return jsonify({"success": False, "msg": "Error"})
    print('Secret key reset successful')
    return jsonify({"success": True, "msg": data})
 
# Metamask
@app.route("/metamask", methods=["GET"])
def metamask():
    return render_template("metamask.html")

# Dashboard
@app.route("/dashboard")
def dashboard():
    return render_template("dashboard.html", **locals())


# Auth or Register
@app.route('/auth', methods=['POST'])
def auth():
    data = request.get_json()
    try:
        users = db.child("users").order_by_child("address").equal_to(
            data['address']).limit_to_last(1).get()
        for user in users.each():
            session['usr'] = user.val()["address"]
        return jsonify({"success": True, "msg": "User is registered."})
    except:
        push_data = {"address": data['address'], "secret": uuid.uuid4().hex, "email": ""}
        response = db.child("users").push(push_data)
        return jsonify({"success": True, "msg": response['name']})


# Search for Receipent Address
@app.route('/search', methods=['POST'])
def search():
    data = request.get_json()
    user_address = ""
    try:
        if "@" in data['recipient']:
            users = db.child("users").order_by_child("email").equal_to(
              data['recipient']).limit_to_last(1).get()
        else:
            users = db.child("users").order_by_child("address").equal_to(
              data['recipient']).limit_to_last(1).get()
        for user in users.each():
            user_address = user.val()["address"]
        if data['senderAddress'] == user_address:
            print('Cannot send to your own address')
            return jsonify({"success": False, "msg": "Cannot send to your own address"})
        return jsonify({"success": True, "msg": user_address})
    except:
        print('User Not found')
        return jsonify({"success": False, "msg": "User Not found"})


# Transaction Histroy
@app.route('/history', methods=['POST'])
def history():
    data = request.get_json()
    user_address = ""
    try:
        users = db.child("users").order_by_child("address").equal_to(
            data['senderAddress']).limit_to_last(1).get()
        for user in users.each():
            user_address = user.val()["address"]
    except:
        print('User Not found')
        return jsonify({"success": False, "msg": "User Not found"})

    try:
        latest_txns = []
        txns = db.child("txn").order_by_child("senderAddress").equal_to(
            user_address).limit_to_last(6).get()
        for txn in reversed(txns.each()):
            latest_txns.append(txn.val())
        return jsonify({"success": True, "msg": latest_txns})
    except:
        print('No Transactions Found')
        return jsonify({"success": False, "msg": "No Transactions Found"})


# Record Transaction
@app.route('/transfer', methods=['POST'])
def transfer():
    data = request.get_json()
    txnid = db.child("txn").push(data)
    return jsonify({"success": True, "msg": txnid['name']})


# API Checkout
@app.route("/checkout", methods=["POST"])
def checkout():
    try:
        currency = request.form["currency"]
        amt = float(request.form["amt"])
        recipientAddress = request.form["recipientAddress"]  # merchant ID
        secret = request.form["secret"]  # secret key
        successredirecturl = request.form["successredirecturl"]
        failredirecturl = request.form["failredirecturl"]
        notes = request.form["notes"] if request.form["notes"] != None else ""

        print("checkout received: ", currency, amt, recipientAddress, secret,
              successredirecturl, failredirecturl, notes)

    except:
        print('Empty parameters!!!')
        return jsonify({"success": False, "msg": "Empty parameters!!!"})

    try:
        # check if merchant exists
        merchant = ""
        users = db.child("users").order_by_child("address").equal_to(
            recipientAddress).limit_to_last(1).get()
        for user in users.each():
            merchant = user.key()

        if merchant:

            # check secret key of merchant
            user_secret = str(
                db.child("users").child(merchant).get().val()['secret'])
            if user_secret == secret:
                order_data = {
                    "senderAddress": '',
                    "recipientAddress": recipientAddress,
                    "currency": currency,
                    "amt": amt,
                    "successredirecturl": successredirecturl,
                    "failredirecturl": failredirecturl,
                    "notes": notes,
                    "txnID": "",
                    "status": 1
                }
                orderid = db.child("orders").push(order_data)
                return render_template("metamask.html", order_id=orderid['name'])
                # return redirect(url_for('order', order_id=orderid['name']))
                # return jsonify({"success": True, "msg": orderid['name']})
            else:
                print('Invalid Secret Key')
                return jsonify({"success": False, "msg": "Invalid Secret Key"})
        else:
            print('Merchant Not Found')
            return jsonify({"success": False, "msg": "Merchant Not Found"})
    except:
        print('Not able to insert order')
        return jsonify({"success": False, "msg": "Not able to insert order"})


# API order
@app.route("/order/<order_id>", methods=["GET"])
def order(order_id):
    try:
        order = db.child("orders").child(order_id).get().val()
        order_status = order['status']
        recipientAddress = order['recipientAddress']
        amt = round(float(order['amt']), 2)
        currency = order['currency']
        failredirecturl = order['failredirecturl']
        successredirecturl = order['successredirecturl']

        # prepare external redirect URLs
        if successredirecturl is not None:
            if successredirecturl.find(
                    "http://") != 0 and successredirecturl.find(
                        "https://") != 0:
                successredirecturl = "http://" + successredirecturl
        if failredirecturl is not None:
            if failredirecturl.find("http://") != 0 and failredirecturl.find(
                    "https://") != 0:
                failredirecturl = "http://" + failredirecturl

    except:
        print('Empty parameters!!!')
        return jsonify({"success": False, "msg": "Empty parameters!!!"})

    return render_template("order.html", **locals())


# API order
@app.route("/updateorder", methods=["POST"])
def updateorder():
    data = request.get_json()
    print(data)
    update_data = {
        "status": data["status"],
        "senderAddress": data["senderAddress"],
        "txnID": data["txnID"]
    }
    db.child("orders").child(data["orderid"]).update(update_data)
    return jsonify({"success": True, "msg": "Order Updated"})


# SAMPLE WEBSITE ------------------------------------

@app.route("/website")
def website():
    return render_template('simulator/index.html')


@app.route("/websitecart")
def websitecart():
    return render_template('simulator/cart.html')


@app.route("/websitesuccess")
def websitesuccess():
    return render_template('simulator/success.html')


@app.route("/websitefailure")
def websitefailure():
    return render_template('simulator/failure.html')

    # status 1 = Order Created
    # status 2 = Transfer Complete
    # status 3 = Transfer Failed
    # status 4 = Expired
    # status 5 = Refund Initated
    # status 6 = Refunded

app.run(host='0.0.0.0', port=8080, debug=True)
