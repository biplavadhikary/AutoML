import os
from flask import Flask , render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
print("Hello")

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filestorage.db'
db = SQLAlchemy(app)

class FileContents(db.Model):
    id = db.Column(db.Integer,primary_key=True)
    name = db.Column(db.String(300))
    data = db.Column(db.LargeBinary)

#db.create_all()

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/handleUpload',methods=['POST'])
def handleUpload():
    f = request.files['dataset']
    f.save(os.path.join('C:/Users/KIIT/Desktop/AutoML/datasets', f.filename))
    return 'Uploaded {}!!!'.format(f.filename)

if __name__ == "__main__":
    app.run(debug=True)