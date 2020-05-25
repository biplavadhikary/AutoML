import os
from flask import Flask , render_template, request, url_for, redirect, session, send_from_directory
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime

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
    modelClfExists = db.Column(db.Boolean, default=False)
    vizPlotsExists = db.Column(db.Boolean, default=False)
    modelRegExists = db.Column(db.Boolean, default=False)
    accuracyClf = db.Column(db.Float, default=0)
    accuracyReg = db.Column(db.Float, default=0)

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
    session['modelClfExists'] = False
    session['vizPlotsExists'] = False
    session['modelRegExists'] = False
    session['accuracyClf'] = 0.0
    session['accuracyReg'] = 0.0

    # save to db for later use
    new_dataset = FileContents(id=hashCode,name=trueName,attrib_list=str(attr))
    try:
        db.session.add(new_dataset)
        db.session.commit()
        return redirect(url_for('select',showDatasetName='0'))

    except Exception as e:
        return render_template('errorDisplay.html', error={
            'code': 'Error',
            'title': 'Database Commit Error',
            'info': 'An error occured while committing to the database. Please contact the admin'
        })

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
            import scriptViz as vs
            print('Plotting Started ..... ')
            plottypes = vs.buildPng(folderName, target)
            default = lambda o: f"<<non-serializable: {type(o).__qualname__}>>"
            with open(f'./datasets/{folderName}/plotTypes.json', 'w') as outfile:
                json.dump(plottypes, outfile, indent=4, default=default)
            print('Plotting Finished ')
            try:
                info = db.session.query(FileContents).filter_by(id=session['datasetName'].split('_')[0]).scalar()
                info.vizPlotsExists = 1
                db.session.commit()
                session['vizPlotsExists'] = True
            except:
                return render_template('errorDisplay.html', error = {
                    'code': 'Database Error',
                    'title': 'Error while updating value to database',
                    'info': 'Please contact administrator'
                    })


        else:
            if (session['vizPlotsExists'] == False):
                return render_template('errorDisplay.html', error = {
                    'code': 'Error',
                    'title': 'Vizualization data does not Exists',
                    'info': 'Please create the Visualization Data first from the Selection Window'
                })

        plottypes = None
        with open(f'./datasets/{folderName}/plotTypes.json') as infile:
            plottypes = json.load(infile)
        return render_template('visualize.html',folderName=folderName,plottypes=plottypes)

    # regression processing
    elif problem == 'prediction':
        acc = session['accuracyReg']

        # create a model right now
        if session['load_model'] != 'on':
            from scriptReg import generateRegModel
            try:
                acc = generateRegModel(folderName, target, int(session['timer'])/60)
            except RuntimeError:
                return render_template('errorDisplay.html', error = {
                    'code': 'Max Time',
                    'title': 'Cannot build pipeline in the specified Max time',
                    'info': 'Please increase the Timer to a greater number'
                })

            try:
                info = db.session.query(FileContents).filter_by(id=session['datasetName'].split('_')[0]).scalar()
                info.modelRegExists = 1
                info.accuracyReg = acc
                db.session.commit()
                session['modelRegExists'] = True
                session['accuracyReg'] = acc
            except:
                return render_template('errorDisplay.html', error = {
                'code': 'Database Error',
                'title': 'Error while updating value to database',
                'info': 'Please contact administrator'
            })

        # if model exists then display it [common part for both load and create option]
        if (session['modelRegExists'] == False):
            return render_template('errorDisplay.html', error = {
                'code': 'Error',
                'title': 'Model does not Exists',
                'info': 'Please create the Model first from the Selection Window'
            })
        else:
            code, log = '',''
            with open(f'./datasets/{folderName}/pipelineReg.py', 'r') as codeFile, \
                    open(f'datasets/regLogs/{folderName}.txt', 'r') as logFile:
                code = codeFile.read().replace('\\', '&#92;')
                log = logFile.read().replace('\n', '<br>').replace('\\', '&#92;')

            return render_template('modelDisplay.html',folderName=folderName, code=code, log=log, acc=acc)

    # classification processing
    else:
        acc = session['accuracyClf']

        # create a model now
        if session['load_model'] != 'on':
            from scriptClf import generateClfModel
            try:
                acc = generateClfModel(folderName, target, int(session['timer'])/60)
            except RuntimeError:
                return render_template('errorDisplay.html', error = {
                    'code': 'Max Time',
                    'title': 'Cannot build pipeline in the specified Max time',
                    'info': 'Please increase the Timer to a greater number'
                })

            try:
                info = db.session.query(FileContents).filter_by(id=session['datasetName'].split('_')[0]).scalar()
                info.modelClfExists = 1
                info.accuracyClf = acc
                db.session.commit()
                session['modelClfExists'] = True
                session['accuracyClf'] = acc
            except:
                return render_template('errorDisplay.html', error = {
                    'code': 'Database Error',
                    'title': 'Error while updating value to database',
                    'info': 'Please contact administrator'
                    })


        # if model exists then display it [common part for both load and create option]
        if (session['modelClfExists'] == False):
            return render_template('errorDisplay.html', error = {
                'code': 'Error',
                'title': 'Model does not Exists',
                'info': 'Please create the Model first from the Selection Window'
            })

        else:
            code, log = '',''
            with open(f'./datasets/{folderName}/pipelineClf.py', 'r') as codeFile, \
                    open(f'datasets/clfLogs/{folderName}.txt', 'r') as logFile:
                code = codeFile.read().replace('\\', '&#92;')
                log = logFile.read().replace('\n', '<br>').replace('\\', '&#92;')

            return render_template('modelDisplay.html',folderName=folderName, code=code, log=log, acc=acc)

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
        from scriptReg import predict_csv_reg
        status = predict_csv_reg(folderName, target)

    else:
        from scriptClf import predict_csv_clf
        status = predict_csv_clf(folderName, target)

    if (status == True):
        return render_template('table.html', testURL=testURL, folderName=folderName)
    else:
        return render_template('errorDisplay.html', error = {
            'code': 'Error',
            'title': 'Required Model not Found',
            'info': 'Make sure you have created the Model previously'
        })

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

            # inform the session of existence of a model
            setModelExistenceInfo(dataid = session['datasetName'].split('_')[0])

            return redirect(url_for('select',showDatasetName='1'))

@app.route('/about')
def renderAbout():
    return render_template('about.html')

@app.errorhandler(404)
def pageNotFound(e):
    return render_template('errorDisplay.html', error = {
        'code': '404',
        'title': 'Page does not Exists',
        'info': 'Please check if the URL is correct'
    })

def setModelExistenceInfo(dataid):
    x = db.session.query(FileContents).filter_by(id=dataid).scalar()

    session['modelClfExists'] = x.modelClfExists
    session['vizPlotsExists'] = x.vizPlotsExists
    session['modelRegExists'] = x.modelRegExists
    session['accuracyClf'] = x.accuracyClf
    session['accuracyReg'] = x.accuracyReg

if __name__ == "__main__":
    app.run(host= '0.0.0.0', debug=True)

def create_app():
    return app