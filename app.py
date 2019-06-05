import os
import random
from PIL import Image
from flask import Flask, render_template, redirect, url_for, request, flash
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileAllowed, FileRequired
from wtforms import StringField, PasswordField, BooleanField, DecimalField
from wtforms.validators import InputRequired, Length
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from flask_login import LoginManager, UserMixin, login_user, login_required, logout_user, current_user
from flask_uploads import UploadSet, IMAGES, configure_uploads

app = Flask(__name__)
app.config['SECRET_KEY'] = 'AC152FBA7A4A876228C3C227FC679'
app.config['SQLALCHEMY_DATABASE_URI'] = r'sqlite:///C:\Users\dewijones\PycharmProjects\week5B\market.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

UPLOAD_FOLDER = 'C:\\Users\\dewijones\\PycharmProjects\\week5B\\static\\img\\'
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
Bootstrap(app)

APP_ROOT = os.path.dirname(os.path.abspath(__file__))

db = SQLAlchemy(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

# Folder location to save images
path = r'C:\Users\dewijones\PycharmProjects\week5B\static\img'
UPLOAD_FOLDER_DATABASE = 'img/'
ALLOWED_EXTENSIONS = {'jpg', 'JPG', 'png', 'PNG', 'jpeg', 'JPEG', 'gif', 'GIF'}
# Config Flask-Upload
photos = UploadSet('photos', IMAGES)
app.config['UPLOADED_PHOTOS_DEST'] = path
configure_uploads(app, photos)



class User(UserMixin, db.Model):
    __tablename__ = "users"
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True)
    password = db.Column(db.String(80))
    gold = db.Column(db.Numeric(10, 2), nullable=False, server_default='50.00')

class Inventory(db.Model):
    __tablename__ = "inventory"
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(50), nullable=False, unique=False)
    value = db.Column(db.Numeric(10, 2), nullable=False, server_default='00.00')
    img_location = db.Column(db.String(250), nullable=False, unique=False)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    user = db.relationship("User")

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class LoginForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm):
    username = StringField('Username', validators=[InputRequired(), Length(min=4, max=20)])
    password = PasswordField('Password', validators=[InputRequired(), Length(min=6, max=80)])

class InventoryForm(FlaskForm):
    name = username = StringField('Name', validators=[InputRequired(), Length(min=4, max=50)])
    value = DecimalField('Cost', places=2, validators=[InputRequired()])
    upload = FileField('Image', validators=[FileRequired(), FileAllowed(['jpg', 'JPG', 'png', 'PNG', 'jpeg', 'JPEG', 'gif', 'GIF'], 'Images only!')])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user:
            if check_password_hash(user.password, form.password.data):
                login_user(user, remember=form.remember.data)
                return redirect( url_for('dashboard'))

        return '<h1> Invalid username or password </h1>'

    return render_template('login.html', form=form)

@app.route('/signup', methods=['GET', 'POST'])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        hashed_password = generate_password_hash(form.password.data, method='sha256')
        new_user = User(username=form.username.data, password=hashed_password)
        db.session.add(new_user)
        db.session.commit()
        return redirect(url_for('login'))

    return render_template('signup.html', form=form)

@app.route('/dashboard')
@login_required
def dashboard():
    page = request.args.get('page', 1, type=int)
    per_page = 4
    inventory = Inventory.query.order_by(Inventory.name.asc()).paginate(page, per_page, error_out=False)
    return render_template('dashboard.html', name=current_user.username, id=current_user.id, inventory=inventory)

def allowed_file(filename):
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/profile', methods=['GET', 'POST'])
@login_required
def profile():
    form = InventoryForm()

    if request.method == 'POST':
        form_filename = form.upload.data.filename

        # if user does not select file, browser also
        # submit a empty part without filename
        if form.upload.data.filename == '':
            return redirect(request.url)

        if form.upload.data and allowed_file(form_filename):
            filename = secure_filename(form.upload.data.filename)

            file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
            database_path = os.path.join(UPLOAD_FOLDER_DATABASE, filename)
            form.upload.data.save(file_path)

            new_record = Inventory(name=form.name.data, value=form.value.data, img_location=database_path, user_id=current_user.get_id() )
            db.session.add(new_record)
            db.session.commit()

            return redirect(url_for('dashboard'))
    return render_template('profile.html', form=form)

@app.route('/buy', methods=['GET','POST'])
@login_required
def buy():
    item = Inventory.query.get_or_404(request.form['ItemId'])
    buyer = User.query.get_or_404(current_user.id)
    seller = User.query.get_or_404(item.user_id)

    if buyer.gold <= item.value:
        flash('Not enough silkcoins')
        return redirect('dashboard')

    # Pay for the item
    buyer.gold = buyer.gold - item.value

    # Seller gets the money
    seller.gold = seller.gold + item.value

    db.session.delete(item)
    db.session.commit()

    flash('Nice buy')
    return redirect('dashboard')

@app.route('/account')
@login_required
def account():
    buyer = User.query.get_or_404(current_user.id)
    return render_template('account.html', username=current_user.username, coins=buyer.gold)

@app.route('/create_item', methods=['POST'])
@login_required
def create_item():

    RANDOM_FOLDER_FOR_IMAGES = 'C:\\Users\\dewijones\\PycharmProjects\\week5B\\static\\random_img\\'

    a_random_file = random.choice(os.listdir(RANDOM_FOLDER_FOR_IMAGES ))
    file_path = os.path.join(RANDOM_FOLDER_FOR_IMAGES, a_random_file)
    image = Image.open(file_path)

    new_file_path = os.path.join(UPLOAD_FOLDER, a_random_file)
    image.save(new_file_path)

    database_path = os.path.join(UPLOAD_FOLDER_DATABASE, a_random_file)

    new_record = Inventory(name='Generated', value=random.randint(1, 5), img_location=database_path,
                           user_id=current_user.get_id())
    db.session.add(new_record)
    db.session.commit()

    return redirect(url_for('dashboard'))


@app.route('/add_gold', methods=['POST'])
@login_required
def add_gold():
    buyer = User.query.get_or_404(current_user.id)

    buyer.gold += 5

    db.session.add(buyer)
    db.session.commit()

    return redirect( url_for('account'))

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

if __name__ == '__main__':
    app.run(debug=True)