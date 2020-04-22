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
    return send_from_directory(app.config['DATASET_FOLDER'], filename)

class FileContents(db.Model):
    id = db.Column(db.String(300),primary_key=True)
    name = db.Column(db.String(300))
    attrib_list = db.Column(db.String(500))
    date_created = db.Column(db.DateTime, default=datetime.utcnow)
    completed = db.Column(db.Integer, default=0)
    #data = db.Column(db.LargeBinary)

    def __repr__ (self):
        return f'<Added {self.id}>'

#db.create_all() #use it to create db

@app.route('/')
def index():
    return render_template('index.html', noDataset=False, wrongToken=False)

@app.route('/handleUpload',methods=['POST'])
def handleUpload():
    #f = request.files['dataset']
    if request.files['dataset'].filename == '':
        return render_template('index.html', noDataset=True, wrongToken=False)
    else:
        f = request.files.get('dataset')

    from dataProc import generateHash,addPrefix,extractAttribList
    # generate a unique filename to make it thread safe
    trueName = f.filename
    hashCode = generateHash(trueName)
    uniqueName = addPrefix(hashCode, trueName)
    f.save(os.path.join('C:/Users/KIIT/Desktop/AutoML/datasets', uniqueName))

    # extracting the attributes from header and save it to sesssion
    attr = extractAttribList('C:/Users/KIIT/Desktop/AutoML/datasets/'+uniqueName)
    session['dataset'] = attr
    session['datasetTrueName'] = trueName #name without hash
    session['datasetName'] = uniqueName

    # save to db for later use
    new_dataset = FileContents(id=hashCode,name=trueName,attrib_list=str(attr))
    try:
        db.session.add(new_dataset)
        db.session.commit()
        return redirect(url_for('select',showDatasetName='0'))
    except Exception as e:
        return 'Some error occured: ' + str(e)

@app.route('/select/<showDatasetName>')
def select(showDatasetName):
    # retreive the attribute names from session cookies
    attrib = ''
    if 'dataset' in session.keys():
        attrib = session['dataset']
    else:
        attrib = ['Upload your dataset first', 'Go Back To Index']

    if showDatasetName == '0':
        return render_template('selection.html',attrib=attrib,showDatasetName=False)
    elif showDatasetName == '1':
        return render_template('selection.html',attrib=attrib,showDatasetName=True)

@app.route('/plot')
def plot():
    problem = session['option']

    if problem == 'visualization':
        target = session['target_y']
        folderName = session['datasetName'].split('.')[0]
        import visualizeScript as vs
        print('Plotting Started ..... ')
        plottypes = vs.buildSvg(folderName,target)
        print('Plotting Finished ')
        return render_template('visualize.html',folderName=folderName,plottypes=plottypes)
    elif problem == 'prediction':
        if session['load_model'] == 'on':
            return '<h1>Prediction (Load) is coming in Future</h1>'
        else:
            return redirect(url_for('renderCsv'))
    else:
        if session['load_model'] == 'on':
            return '<h1>Classification (Load) is coming in Future</h1>'
        else:
            #return '<h1>Classification (Create) is coming in Future</h1>'
            return redirect(url_for('renderCsv'))

@app.route('/plot-proc',methods=['POST'])
def plotProc():
    if request.method == 'POST':
        session['option'] = request.form.get('problem')
        session['target_y'] = request.form.get('target_y')
        session['load_model'] = request.form.get('load_model') or 'off'
        return render_template('preloading.html')

@app.route('/render-csv',methods=['GET'])
def renderCsv():
    if request.method == 'GET':
        return render_template('table.html')

@app.route('/checkToken', methods=['POST'])
def checkToken():
    if request.method == 'POST':
        hashCode = request.form.get('tokenCode').strip()
        exists = db.session.query(FileContents.name).filter_by(id=hashCode).scalar()
        if exists is None:
            return render_template('index.html', noDataset=False, wrongToken=True)
        else:
            uniqueName = hashCode + '_' + exists
            from dataProc import extractAttribList
            attr = extractAttribList('C:/Users/KIIT/Desktop/AutoML/datasets/'+uniqueName)
            session['dataset'] = attr
            session['datasetTrueName']  = exists
            session['datasetName'] = uniqueName
            return redirect(url_for('select',showDatasetName='1'))

if __name__ == "__main__":
    app.run(debug=True)