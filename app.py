from flask import Flask, render_template

app = Flask(__name__)
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
  app.run(debug=True)
