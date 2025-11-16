from flask import Flask, render_template, redirect, url_for, request, session, flash, get_flashed_messages
from flask_sqlalchemy import SQLAlchemy


app = Flask(__name__)
app.secret_key = 'SecretStuff'
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///ordersDatabase.sqlite3"
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False


# setting up SQL table 
db = SQLAlchemy(app)

class totalOrders(db.Model):
    _id = db.Column("id", db.Integer, primary_key = True)
    orderName = db.Column(db.String)
    order = db.Column(db.String)
    isReady = db.Column(db.Boolean)


    def __init__(self, orderName, order, isReady):
        self.orderName = orderName
        self.order = order 
        self.isReady = isReady





# subroutines
# 'cleans up' the order, by removing underscores, etc.
def cleanupOrder():
    ordercleaned = []
    for item in session['order']:
        itemCount = session['order'].count(item)
        if itemCount > 1:
            formattedItem = str(itemCount)+'*'+item
            if formattedItem not in ordercleaned:
                ordercleaned.append(formattedItem)
        else:
            ordercleaned.append(item)
    return ordercleaned

# turns each item in an array into a string with line breaks in between 
def makeString(array):
    string = ''
    for item in array:
        string += (item + '<br>')
    return string





# Webpages and logic 

# Order Page 
@app.route('/', methods=['GET','POST'])
@app.route('/order', methods=['GET','POST'])
def order():
        
    if request.method == 'POST':
        
        # get the button request 
        keys= request.form.keys()
        for key in keys:
            item = key


        # resolve clearing basket 
        if item == 'clear':
            session.pop('order', None)

        # resolve going to basket 
        elif item == 'basket':
            if 'orderName' not in session:
                flash('Please enter a name first.')
            elif 'order' not in session:
                flash('You must add some items to the basket first!')
            else:
                return redirect(url_for('basket'))

        # resolve order name entry 
        elif item == 'submitName':
            entry = request.form['orderName']
            entryStrippped = entry.strip()
            if entryStrippped == '':
                if 'orderName' in session:
                    session.pop('orderName', None)
            else:
                if 'orderName' in session:
                    if session['orderName'] == entry:
                        session['orderName'] = entry 
                    else:
                        session['orderName'] = entry 
                        flash('Order name updated!')
                else:
                    session['orderName'] = entry   
                    flash('Order name created!')
            
        
        # if food is ordered 
        else:
            flash(item + ' has been added to your Order!')
            if 'order' not in session: 
                session['order'] = [item]
            
            else:
                item_list = session['order']
                item_list.append(item)
                session['order'] = item_list


    # calculates the basket size 
    if 'order' in session:
        basketSize = len(session['order'])
    else: 
        basketSize = 0  

    #displays the page, either with the order name or not in bottom bar
    if 'orderName' in session:
        return render_template('order.html', number=basketSize, orderName=session['orderName'])
    else:
        return render_template('order.html', number=basketSize)



# Basket Page (must have an order and order name to enter)
@app.route('/basket', methods=['GET','POST'])
def basket():

    #redirects if there is no order made 
    if 'order' not in session or 'orderName' not in session:
        return redirect(url_for('order'))
    
    if request.method == 'POST':
        keys= request.form.keys()
        for key in keys:
            itemRemove = key


        # Confirms order and adds the order to database 
        if itemRemove == 'submitOrder':
            totalOrder = totalOrders(session['orderName'], makeString(cleanupOrder()), False)
            db.session.add(totalOrder)
            db.session.commit()

            return redirect(url_for('purchase'))

        #removes the desired item from the basket
        else:
            for item in session['order']:
                if item in itemRemove:
                    orderTemp = session['order']
                    orderTemp.remove(item)
                    session['order'] = orderTemp
                    break


    # 'cleans up' the order so that it looks better when displayed
    ordercleaned = cleanupOrder()

    # clears the order from the session and redirects back to order page
    if len(session['order']) == 0:
        session.pop('order',None)
        return redirect(url_for('order'))
    return render_template('basket.html', name=session['orderName'], order=ordercleaned)



#purchase complete page
@app.route('/purchase')
def purchase():
    #redirect the user if they have not got anything in basket. 
    if 'orderName' not in session or 'order' not in session:
        return redirect(url_for('order'))


    # finds all orders in database with the order name in attempt to find the id
    ordersWithName=totalOrders.query.filter(totalOrders.orderName == session['orderName'])

    #finds the id of the most recent order placed with said name. 
    # was it even necessary to get the name as could have just used last element ?
    for item in ordersWithName:
        yourOrderID = item._id
    yourOrderName = session['orderName']

    #clears the session and displays the 'receipt'. 
    session.pop('order',None)
    session.pop('orderName', None)
    return render_template('purchase.html',id=yourOrderID, name=yourOrderName)



# fulfilment page 
@app.route('/fulfilment',methods=['GET','POST'])
def fulfilment():
    

    if request.method == 'POST':
        ids = request.form.keys()
        for item in ids:
            idOrder = item
            print('name check', idOrder)


        #identifies that the button was indicating a collected order and so removes it
        if int(idOrder) < 0: 
            print('omg', idOrder)
            idOrder = int(idOrder) * -1
            print('reformed', idOrder) 
            totalOrders.query.filter(totalOrders._id == idOrder).delete()
            db.session.commit()


        #identifies that the button press wants to clear all orders and does so 
        elif idOrder == 'clear':
            totalOrders.query.filter(totalOrders.isReady == True).delete()
            db.session.commit()


        # either makes bool isReady True or False depending on its current state
        else:
            orderToEdit = totalOrders.query.filter_by(_id = idOrder).first()
            orderToEdit.isReady = not orderToEdit.isReady
            db.session.commit()

    
    ordersToPrepare = totalOrders.query.filter(totalOrders.isReady == False)
    preparedOrders = totalOrders.query.filter(totalOrders.isReady == True)
    
    return render_template("fulfilment.html", OrdersToPrepare=ordersToPrepare, PreparedOrders=preparedOrders)




@app.route('/progress')
def progress():
    #displays the progress page
    return render_template("progress.html", OrdersToPrepare=totalOrders.query.filter(totalOrders.isReady == False), PreparedOrders=totalOrders.query.filter(totalOrders.isReady == True))







# # Dev clear session page 
# @app.route('/clear')
# def clear():
#     session.pop('order',None)
#     session.pop('orderName', None)
#     db.session.query(totalOrders).delete()
#     db.session.commit()
#     return redirect(url_for('order'))





# Main body 
if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='192.168.0.233', port=5000, debug=True, threaded=False)

