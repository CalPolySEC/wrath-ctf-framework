from flask import Flask, render_template, request


app = Flask(__name__)


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/login')
def join_team():
    return render_template('join.html')


@app.route('/submit')
def submit_flag():
    return render_template('submit.html')


@app.route('/about')
def about():
    return render_template('about.html')


@app.route('/contact')
def contact():
    return render_template('contact.html')


if __name__ == '__main__':
    app.run(debug=True)
