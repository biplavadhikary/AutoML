import os
from flask import Flask , render_template, request, url_for, redirect
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
    return render_template('index.html',warn=False)

@app.route('/handleUpload',methods=['POST'])
def handleUpload():
    #f = request.files['dataset']
    if request.files['dataset'].filename == '':
        return render_template('index.html',warn=True)
    else:
        f = request.files.get('dataset')
    f.save(os.path.join('C:/Users/KIIT/Desktop/AutoML/datasets', f.filename))
    print('Uploaded {}!!!'.format(f.filename))
    return redirect(url_for('select'))

@app.route('/select')
def select():
    return render_template('selection.html')

"""@app.route('/plot')
def plot():
    import authcharts
    return authcharts.basicplt()"""

if __name__ == "__main__":
    app.run(debug=True)