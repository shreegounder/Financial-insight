from flask import Flask, jsonify

app = Flask(__name__)


@app.route('/', methods=['POST'])
def generate_text():
    return jsonify({"response": "hi world!"})


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=3000, debug=True)
