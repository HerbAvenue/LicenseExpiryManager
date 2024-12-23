from flask import Flask, render_template, session, redirect, url_for, request, flash
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import Date
from werkzeug.security import generate_password_hash, check_password_hash
from datetime import datetime
from sqlalchemy.orm import relationship, backref

#Deploy Flask
app = Flask(__name__)
app.secret_key = "LicManagerKey"

#Configure SQLAlchemy
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///licmanager.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)

#Create Databases
#Users Table
class User(db.Model):
    __tablename__ = 'users'
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(25), unique=True, nullable=False)
    password_hash = db.Column(db.String(150), nullable=False)
    licenses = relationship('License', backref='user', lazy=True)

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

#Licenses Table
class License(db.Model):
    __tablename__ = 'licenses'
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    name = db.Column(db.String(50), nullable=False)  # e.g., "Credit Card - Visa"
    expiry = db.Column(Date, nullable=False)

    def __repr__(self):
        return f'<License {self.name} - Expiry: {self.expiry}>'

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
    username = request.form['username'].upper()
    password = request.form['password']
    user = User.query.filter_by(username=username).first()
    
    #Check login info in DB
    if user and user.check_password(password):
        
        ##LEARN WTF SESSION REALLY DOES ?!?!?!?
        session['username'] = username
        return redirect(url_for('dashboard'))
    
    #Else, show homepage
    else:
        return render_template('index.html', error="Invalid Credentials")

#Register
@app.route('/register', methods=["POST"])
def register():
    username = request.form['username'].upper()
    password = request.form['password']
    user = User.query.filter_by(username=username).first()

    if not username or not password:
        return 'You need to enter a username and password'
    
    if user:
        return render_template('index.html', error='User Already Exists')
    else:
        new_user = User(username=username)
        new_user.set_password(password)
        db.session.add(new_user)
        db.session.commit()
        session['username'] = username
        return redirect(url_for('dashboard'))

#Dashboard
@app.route('/dashboard', methods=["GET", "POST"])
def dashboard():
    if "username" not in session:
        return redirect(url_for('index'))

    user = User.query.filter_by(username=session['username']).first()

    if request.method == "POST":
        # Get data from the form
        license_type = request.form.get('license-type')
        specific_type = request.form.get('credit-card-type') or \
                        request.form.get('specific-license-type') or \
                        request.form.get('membership-name')
        expiry_date = request.form.get('expiry-date')

        # Validate data
        if not license_type or not specific_type or not expiry_date:
            flash("All fields are required!", "error")
            return redirect(url_for('dashboard'))

        # Parse expiry date and save to the database
        try:
            expiry_date_obj = datetime.strptime(expiry_date, "%Y-%m-%d").date()
        except ValueError:
            flash("Invalid date format!", "error")
            return redirect(url_for('dashboard'))

        new_license = License(
            user_id=user.id,
            name=f"{license_type} - {specific_type}",
            expiry=expiry_date_obj
        )
        db.session.add(new_license)
        db.session.commit()
        flash("License added successfully!", "success")

    # Fetch licenses for the logged-in user
    licenses = License.query.filter_by(user_id=user.id).order_by(License.expiry).all()

    return render_template('dashboard.html', username=session['username'], licenses=licenses)


#Logout
@app.route('/logout')
def logout():
    session.pop('username')
    return redirect(url_for('index'))

#Creates databases when running app.py directly
if __name__ == "__main__":
    with app.app_context():
        db.create_all()
        print('Database Initialized.')