import os
from flask import Flask , render_template, request, url_for, redirect, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
from visualizeScript import buildSvg

app = Flask(__name__)
#app.config['SECRET_KEY'] = os.urandom(24)
app.config['SECRET_KEY'] = b'\x8d[\xea\xfa\xa2?\x7fg\xa7\xad\xe1\xf4NhUu\xe1\xa8\xd9,*C\x8f\xb0'
app.config['DATASET_FOLDER'] = './datasets'
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///filestorage.db'
db = SQLAlchemy(app)

@app.route('/datasets/<path:filename>', methods=["GET"])
def getFile(filename):
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
    f.save(os.path.join('./datasets', uniqueName))

    # create a subfolder for the dataset
    folderName= uniqueName.split('.')[0]
    os.mkdir(f'./datasets/{folderName}') 

    # extracting the attributes from header and save it to sesssion
    attr = extractAttribList('./datasets/'+uniqueName)
    session['dataset'] = attr
    session['datasetTrueName'] = trueName #name without hash
    session['datasetName'] = uniqueName
    popSessionKeys()

    # save to db for later use
    new_dataset = FileContents(id=hashCode,name=trueName,attrib_list=str(attr))
    try:
        db.session.add(new_dataset)
        db.session.commit()
        return redirect(url_for('select',showDatasetName='0'))

    except Exception as e:
        error = {
            'code': 'Error',
            'title': 'Database Commit Error',
            'info': 'An error occured while committing to the database. Please contact the admin'
        }
        return render_template('errorDisplay.html', error=error)

@app.route('/select/<showDatasetName>')
def select(showDatasetName):
    # retreive the attribute names from session cookies
    attrib = ''
    if 'dataset' in session.keys():
        attrib = session['dataset']
    else:
        attrib = ['Upload your dataset first', 'Go Back To Index']

    if ('modelClfExists' not in session.keys()):
        session['modelClfExists'] = False
    if('vizPlotsExists' not in session.keys()):
        session['vizPlotsExists'] = False
    if('modelRegExists' not in session.keys()):
        session['modelRegExists'] = False

    if showDatasetName == '0':
        return render_template('selection.html',attrib=attrib,showDatasetName=False)
    elif showDatasetName == '1':
        return render_template('selection.html',attrib=attrib,showDatasetName=True)

@app.route('/generate-proc',methods=['POST'])
def GenerateProc():
    if request.method == 'POST':
        session['option'] = request.form.get('problem')
        session['target_y'] = request.form.get('target_y')
        session['timer'] = request.form.get('timer')
        session['load_model'] = request.form.get('load_model') or 'off'
        return render_template('preloading.html')

@app.route('/generate')
def generate():
    problem = session['option']
    target = session['target_y']
    folderName = session['datasetName'].split('.')[0]

    # visualization processing
    if problem == 'visualization':
        import json
        if (session['load_model'] != 'on'):
            import visualizeScript as vs
            print('Plotting Started ..... ')
            plottypes = vs.buildSvg(folderName, target)
            with open(f'./datasets/{folderName}/plotTypes.json', 'w') as outfile:
                json.dump(plottypes, outfile, indent=4)
            print('Plotting Finished ')
            session['vizPlotsExists'] = True

        else:
            if (session['vizPlotsExists'] == False):
                error = {
                    'code': 'Error',
                    'title': 'Vizualization data does not Exists',
                    'info': 'Please create the Visualization Data first from the Selection Window'
                }
                return render_template('errorDisplay.html', error=error)

        plottypes = None
        with open(f'./datasets/{folderName}/plotTypes.json') as infile:
            plottypes = json.load(infile)
        return render_template('visualize.html',folderName=folderName,plottypes=plottypes)

    # regression processing
    elif problem == 'prediction':
        
        if session['load_model'] != 'on':
            from regressionScript import generateRegModel
            acc = None
            try:
                acc = generateRegModel(folderName, target, int(session['timer'])/60)
            except RuntimeError:
                error = {
                    'code': 'Max Time',
                    'title': 'Cannot build pipeline in the specified Max time',
                    'info': 'Please increase the Timer to a greater number'
                }
                return render_template('errorDisplay.html', error=error)

            session['modelRegExists'] = True
            session['accuracy'] = acc

        else:
            if (session['modelRegExists'] == False):
                error = {
                    'code': 'Error',
                    'title': 'Model does not Exists',
                    'info': 'Please create the Model first from the Selection Window'
                }
                return render_template('errorDisplay.html', error=error)

        code, log = '',''
        with open(f'./datasets/{folderName}/pipelineReg.py', 'r') as codeFile, \
                open(f'datasets/regLogs/{folderName}.txt', 'r') as logFile:
            code = codeFile.read().replace('\\', '&#92;')
            log = logFile.read().replace('\n', '<br>').replace('\\', '&#92;')

        return render_template('modelDisplay.html',folderName=folderName, code=code, log=log, acc=session['accuracy']*100)

    # classification processing
    else:
        if session['load_model'] != 'on':
            from classificationScript import generateClfModel
            acc = None
            try:
                acc = generateClfModel(folderName, target, int(session['timer'])/60)
            except RuntimeError:
                error = {
                    'code': 'Max Time',
                    'title': 'Cannot build pipeline in the specified Max time',
                    'info': 'Please increase the Timer to a greater number'
                }
                return render_template('errorDisplay.html', error=error)

            session['modelClfExists'] = True
            session['accuracy'] = acc

        else:
            if (session['modelClfExists'] == False):
                error = {
                    'code': 'Error',
                    'title': 'Model does not Exists',
                    'info': 'Please create the Model first from the Selection Window'
                }
                return render_template('errorDisplay.html', error=error)

        code, log = '',''
        with open(f'./datasets/{folderName}/pipelineClf.py', 'r') as codeFile, \
                open(f'datasets/clfLogs/{folderName}.txt', 'r') as logFile:
            code = codeFile.read().replace('\\', '&#92;')
            log = logFile.read().replace('\n', '<br>').replace('\\', '&#92;')

        return render_template('modelDisplay.html',folderName=folderName, code=code, log=log, acc=session['accuracy']*100)

# test route only
@app.route('/modelDisp')
def modelDisp():
    return render_template('modelDisplay.html')

@app.route('/handleTest', methods=['POST'])
def handleTest():
    if request.files['testset'].filename == '':
        return render_template('modelDisplay.html', noDataset=True)
    else:
        f = request.files.get('testset')
        folderName = session['datasetName'].split('.')[0]
        f.save(os.path.join(f'./datasets/{folderName}', 'test.csv'))
        return redirect(url_for('renderTable'))

@app.route('/renderTable')
def renderTable():
    problem = session['option']
    target = session['target_y']
    folderName = session['datasetName'].split('.')[0]
    testURL = f'{folderName}/test_predicted.csv'
    status = None

    if problem ==  'prediction':
        from regressionScript import predict_csv_reg
        status = predict_csv_reg(folderName, target)

    else:
        from classificationScript import predict_csv_clf
        status = predict_csv_clf(folderName, target)

    if (status == True):
        return render_template('table.html', testURL=testURL, folderName=folderName)
    else:
        error = {
            'code': 'Error',
            'title': 'Required Model not Found',
            'info': 'Make sure you have created the Model previously'
        }
        return render_template('errorDisplay.html', error=error)

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
            attr = extractAttribList('./datasets/'+uniqueName)
            session['dataset'] = attr
            session['datasetTrueName']  = exists
            session['datasetName'] = uniqueName
            popSessionKeys()

            return redirect(url_for('select',showDatasetName='1'))

@app.route('/about')
def renderAbout():
    return render_template('about.html')

@app.errorhandler(404)
def pageNotFound(e):
    error = {
        'code': '404',
        'title': 'Page does not Exists',
        'info': 'Please check if the URL is correct'
    }
    return render_template('errorDisplay.html', error=error)

def popSessionKeys():
    if 'modelClfExists' in session.keys():
        session.pop('modelClfExists')
    if 'mvizPlotsExists' in session.keys():
        session.pop('mvizPlotsExists')
    if 'modelRegExists' in session.keys():
        session.pop('modelRegExists')

if __name__ == "__main__":
    app.run(host= '0.0.0.0', debug=True)

def create_app():
    return app