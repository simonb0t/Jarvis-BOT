from flask import Flask, request

app = Flask(__name__)

@app.route("/", methods=["GET"])
def home():
    return "Jarvis está activo 🚀"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Mensaje recibido:", data)
    return "OK", 200

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
