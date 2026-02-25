from flask import Flask, render_template, request
import requests

app = Flask(__name__)

API_URL = "https://api-inference.huggingface.co/models/gpt2"
headers = {"Authorization": "Bearer YOUR_TOKEN_HERE"}

def query(prompt):
    payload = {
        "inputs": prompt,
        "parameters": {"max_new_tokens":100}
    }

    response = requests.post(API_URL, headers=headers, json=payload)

    try:
        data = response.json()
        if isinstance(data, list):
            return data[0]["generated_text"]
        else:
            return str(data)
    except:
        return "Model loading… try again."

@app.route("/", methods=["GET","POST"])
def login():
    if request.method == "POST":
        username = request.form["username"]
        return render_template("home.html",
                               username=username,
                               initial=username[0].upper())
    return render_template("login.html")

@app.route("/generate", methods=["POST"])
def generate():
    username = request.form.get("username","User")
    prompt = request.form["input_text"]
    language = request.form["language"]

    final_prompt = f"Write {language} code: {prompt}"

    output = query(final_prompt)

    return render_template("home.html",
                           username=username,
                           initial=username[0].upper(),
                           output=output)

if __name__ == "__main__":
    app.run(debug=True)