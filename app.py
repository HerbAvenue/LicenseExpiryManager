from flask import Flask, render_template, session, redirect, url_for, request
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date
from werkzeug.security import generate_password_hash, check_password_hash

#Deploy Flask
app = Flask(__name__)
app.secret_key = "LicManagerKey"

#Configure SQLAlchemy
app.config['SQLALCHEMY_BINDS'] = { 
    'db1': 'sqlite:///users.db',
    'db2': 'sqlite:///licenses.db'
}
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Create Databases
class Users(db.Model):
    __bind_key__ = 'db1'
    UserId = db.Column(db.Integer, primary_key = True)
    Username = db.Column(db.String(25), unique=True, nullable = False)
    #Password = db.Column(db.String, nullable = False)
    Password_hash = db.Column(db.String(150), nullable=False)

    def set_password(self, password):
        self.Password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.Password_hash, password)

class Licenses(db.Model):
    __bind_key__ = 'db2'
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(20), nullable=False)
    expiry = db.Column(Date, nullable=False)

    def __repr__(self):
        return '<License %r>' % self.id

#Routes
@app.route('/')
def index():
    if "username" in session:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

#Login
@app.route('/login', methods=["POST"])
def login():
    #Collect login form info
    username = request.form['username']
    password = request.form['password']
    user = Users.query.filter_by(Username=username).first()
    
    #Check login info in DB
    if user and user.check_password(password):
        
        ##LEARN WTF SESSION REALLY DOES ?!?!?!?
        session['username'] = username
        return redirect(url_for('dashboard'))
    
    #Else, show homepage
    else:
        return render_template('index.html')

#Register
@app.route('/register', methods=["POST"])
def register():
    username = request.form['username']
    password = request.form['password']
    user = Users.query.filter_by(Username=username).first()
    if user:
        return render_template('index.html', error='User Already Exists')
    else:
        new_user = Users(Username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))

#Dashboard
@app.route('/dashboard')
def dashboard():
    if "username" in session:
        return render_template('dashboard.html', username=session['username'])



#Logout
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect(url_for('index'))

#Creates databases when running app.py directly
if __name__ == "__main__":
    with app.app_context():
        db.create_all(bind_key=["db1"])
        db.create_all(bind_key=["db2"])

        print('Databases Created.')



##https://www.youtube.com/watch?v=Fr2MxT9M0V4 - T42.45