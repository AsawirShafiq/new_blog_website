from flask import Flask, render_template, redirect, url_for
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, PasswordField, BooleanField, ValidationError
from wtforms.validators import DataRequired, EqualTo, Length
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from datetime import datetime
from werkzeug.security import generate_password_hash, check_password_hash
from wtforms.widgets import TextArea
from flask_login import UserMixin, login_user, LoginManager, login_required, logout_user, current_user
import os
app = Flask(__name__)

app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://user:password@localhost:3306/new_flask_db'
app.config['SECRET_KEY'] = "my secret key"

db = SQLAlchemy(app)
migrate = Migrate(app,db)

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
  return Users.query.get(int(user_id))

#Login form
class LoginForm(FlaskForm):
  username = StringField("username",validators=[DataRequired()])
  password = PasswordField("PAssword",validators=[DataRequired()])
  submit = SubmitField("Submit")

@app.route('/login', methods=['GET','POST'])
def login():
  form = LoginForm()
  if form.validate_on_submit():
    user = Users.query.filter_by(username=form.username.data).first()
    if user:
      if check_password_hash(user.password_hash, form.password.data):
        login_user(user)
        return redirect(url_for('posts'))
  return render_template('login.html', form=form)

#Logout

@app.route('/logout',methods=['GET','POST'] )
@login_required
def logout():
  logout_user()
  return redirect(url_for('login'))


#Creating User model
class Users(db.Model, UserMixin):
  id = db.Column(db.Integer, primary_key=True)
  username = db.Column(db.String(20), nullable= False, unique=True)
  name = db.Column(db.String(200), nullable=False)
  email = db.Column(db.String(120), nullable=False, unique=True)
  favourite_color = db.Column(db.String(120))
  date = db.Column(db.DateTime, default=datetime.utcnow)

  #handling passwords
  password_hash = db.Column(db.String(128))

  @property
  def password(self):
    raise AttributeError('password not a readable attibute')
  @password.setter
  def password(self, password):
    self.password_hash = generate_password_hash(password)
  def verify_password(self,password):
    return check_password_hash(self.password_hash,password)
  # Create a string
  def __repr__(self):
    return '<Name %r>' % self.name

# Blog post model
class Posts(db.Model):
  id = db.Column(db.Integer,primary_key =True)
  title = db.Column(db.String(255))
  content = db.Column(db.Text)
  author = db.Column(db.String(255))
  date_posted =db.Column(db.DateTime, default=datetime.utcnow)
  slug = db.Column(db.String(255))

#Create Post form

class PostForm(FlaskForm):
  title=StringField("Title",validators=[DataRequired()])
  content=StringField("Content",validators=[DataRequired()], widget=TextArea())
  author=StringField("Author",validators=[DataRequired()])
  slug=StringField("Slug",validators=[DataRequired()])
  submit=SubmitField("Submit")

#Show blogs

@app.route('/posts')
@login_required
def posts():
  posts = Posts.query.order_by(Posts.date_posted)
  return render_template("posts.html", posts=posts)

#show one blog
@app.route('/posts/<int:id>')
@login_required
def post(id):
  post = Posts.query.get_or_404(id)
  return render_template("post.html", post=post)

#Edit a blog
@app.route('/posts/edit/<int:id>',methods=['GET','POST'])
@login_required
def edit_post(id):

  post = Posts.query.get_or_404(id)
  form =PostForm()
  if form.validate_on_submit():
    post.title = form.title.data
    post.author = form.author.data
    post.slug = form.slug.data
    post.content = form.content.data

    db.session.add(post)
    db.session.commit()

    return redirect(url_for('post', id=post.id))

  form.title.data = post.title
  form.content.data = post.content
  form.author.data = post.author
  form.slug.data = post.slug
  return render_template("edit_post.html", form=form)

#Delete a post
@app.route('/posts/delete/<int:id>')
@login_required
def delete_post(id):
  post_to_delete = Posts.query.get_or_404(id)
  try:
    db.session.delete(post_to_delete)
    db.session.commit()
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html", posts=posts)
  except:
    posts = Posts.query.order_by(Posts.date_posted)
    return render_template("posts.html", posts=posts)


# Add Post page
@app.route('/add-post', methods=['GET','POST'])
@login_required
def add_post():
  form = PostForm()

  if form.validate_on_submit():
    post = Posts(title=form.title.data, content=form.content.data, author=form.author.data, slug=form.slug.data)
    form.title.data = ''
    form.content.data = ''
    form.author.data = ''
    form.slug.data = ''

    #add to database
    db.session.add(post)
    db.session.commit()

  return render_template("add_post.html", form=form)

#Create a password form
class PasswordForm(FlaskForm):
  email = StringField("Whats your email", validators=[DataRequired()])
  password_hash = PasswordField("Whats your password", validators=[DataRequired()])
  submit = SubmitField("Submit")

#Create a User form class
class UserForm(FlaskForm):
  name = StringField("Name", validators=[DataRequired()])
  username = StringField("Username", validators=[DataRequired()])
  email = StringField("email", validators=[DataRequired()])
  favourite_color = StringField("favourite color")
  password_hash = PasswordField('Password', validators=[DataRequired(), EqualTo('password_hash2', message= 'Passowrds must match')])
  password_hash2 = PasswordField('Confirm Password', validators=[DataRequired()])
  submit = SubmitField("Submit")

@app.route('/user/add', methods=['GET', 'POST'])
def add_user():
  name = None
  form = UserForm()
  if form.validate_on_submit():
    user = Users.query.filter_by(email=form.email.data).first()
    if user is None:
      #Hash the password
      hashed_pw = generate_password_hash(form.password_hash.data, method='pbkdf2:sha256')
      user = Users(name=form.name.data,username=form.username.data ,email=form.email.data, favourite_color=form.favourite_color.data, password_hash=hashed_pw)
      db.session.add(user)
      db.session.commit()
    name = form.name.data
    form.name.data = ''
    form.username.data = ''
    form.email.data = ''
    form.favourite_color.data = ''
    form.password_hash.data = ''
  our_users = Users.query.order_by(Users.date)
  return render_template("add_user.html",
                         form=form,
                         name=name,
                         our_users=our_users)
#DELETE USER
@app.route('/delete/<int:id>')
def delete(id):
  user_to_delete = Users.query.get_or_404(id)
  name = None
  form = UserForm()
  try:
    db.session.delete(user_to_delete)
    db.session.commit()
    our_users = Users.query.order_by(Users.date)
    return render_template("add_user.html",
                         form=form,
                         name=name,
                         our_users=our_users)
  except:
    return "<h1> Errorin delete </h1>"

#Test password
@app.route('/test', methods= ['GET','POST'])
def test_pw():
  email = None
  password = None
  pw_to_check = None
  passed = None
  form = PasswordForm()

  #Validate form
  if form.validate_on_submit():
    email = form.email.data
    password = form.password_hash.data
    form.email.data = ''
    form.password_hash.data = ''

    #Get user by email
    pw_to_check = Users.query.filter_by(email=email).first()

    #Check hashed password
    passed = check_password_hash(pw_to_check.password_hash,password)

  return render_template("pw_test.html",
                         email=email,
                         password=password,
                         pw_to_check=pw_to_check,
                         passed=passed,
                         form=form)


@app.route('/')

def index():
  return render_template("index.html")

@app.route('/user/<name>')

def user(name):
  return render_template("user.html", name = name)

#InVALID URL
@app.errorhandler(404)
def page_not_found(e):
  return render_template("404.html"), 404


#Internal server error
@app.errorhandler(500)
def page_not_found(e):
  return render_template("500.html"), 500

if __name__ == "__main__":
  app.run(host = '0.0.0.0',port = 5000 ,debug=os.environ.get('DEBUG')=='1')
