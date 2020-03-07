import os
from flask import Flask , render_template, request, url_for, redirect, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from visualizeScript import buildSvg

app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
app.config['DATASET_FOLDER'] = './datasets'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filestorage.db'
db = SQLAlchemy(app)

@app.route('/datasets/<path:filename>', methods=["GET"])
def svgRender(filename):
    print('Called here')
    return send_from_directory(app.config['DATASET_FOLDER'], filename)

class FileContents(db.Model):
    id = db.Column(db.String(300),primary_key=True)
    name = db.Column(db.String(300))
    attrib_list = db.Column(db.String(500))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Integer, default=0)
    #data = db.1Column(db.LargeBinary)

    def __repr__ (self):
        return f'<Added {self.id}>'

#db.create_all() #use it to create db

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

    from dataProc import addPrefix,extractAttribList
    # generate a unique filename to make it thread safe
    filenameOr = f.filename
    filenameUn = addPrefix(filenameOr)
    f.save(os.path.join('C:/Users/KIIT/Desktop/AutoML/datasets', filenameUn))

    # extracting the attributes from header and save it to sesssion
    attr = extractAttribList('C:/Users/KIIT/Desktop/AutoML/datasets/'+filenameUn)
    session['dataset'] = attr
    session['datasetName'] = filenameUn

    # save to db for later use
    new_dataset = FileContents(id=filenameUn,name=filenameOr,attrib_list=str(attr))
    try:
        db.session.add(new_dataset)
        db.session.commit()
        return redirect(url_for('select'))
    except Exception as e:
        return 'Some error occured: ' + str(e)

@app.route('/select')
def select():
    # retreive the attribute names from session cookies
    attrib = ''
    if 'dataset' in session.keys():
        attrib = session['dataset']
    else:
        attrib = ['Upload your dataset first', 'Go Back To Index']
    return render_template('selection.html',attrib=attrib)

@app.route('/plot',methods=['POST'])
def plot():  
    if request.method == 'POST':
        target = request.form.get('target_y')
        folderName = session['datasetName'].split('.')[0]
        import visualizeScript as vs
        plottypes = vs.buildSvg(folderName,target)
        return render_template('visualize.html',folderName=folderName,plottypes=plottypes)

if __name__ == "__main__":
    app.run(host='0.0.0.0',debug=True)