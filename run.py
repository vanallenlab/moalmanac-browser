from target_web import create_app

app = create_app(__name__)
app.run(host='0.0.0.0')
