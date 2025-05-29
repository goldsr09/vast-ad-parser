# app_display.py

from flask import Flask, render_template, request
from parser_display import parse_vast

app = Flask(__name__)

@app.route('/', methods=['GET', 'POST'])
def index():
    results = None
    if request.method == 'POST':
        vast_url = request.form.get('vast_url')
        if vast_url:
            results = parse_vast(vast_url)
    return render_template('index.html', results=results)

if __name__ == '__main__':
    app.run(debug=True)
