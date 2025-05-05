import flask

app = flask.Flask(__name__)
@app.route("/")
def home():
  return "Hello Pooja , how are you"

if __name__ == "__main__":
  app.run(debug=True)