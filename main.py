from flask import Flask, request

app = Flask(_name_)

@app.route("/", methods=["GET"])
def home():
    return "Jarvis está activo 🚀"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.json
    print("Mensaje recibido:", data)
    return "OK", 200

if _name_ == "_main_":
    app.run(host="0.0.0.0", port=5000)
