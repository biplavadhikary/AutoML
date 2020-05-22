def generateClfModel(folderName, target_col, timer):
    import pandas as pd
    import os, sys
    from tpot import TPOTClassifier
    from sklearn.preprocessing import LabelEncoder
    from sklearn.model_selection import train_test_split

    #print to logs instead of stdout
    stdoutSave = sys.stdout
    sys.stdout = open(f'datasets/clfLogs/{folderName}.txt', 'w')

    df = pd.read_csv(f'datasets/{folderName}.csv')

    le = LabelEncoder()
    X = df.loc[:, df.columns != target_col].apply(le.fit_transform).values
    Y = df.loc[:, [target_col]].apply(le.fit_transform).values

    X_train, X_test, Y_train, Y_test = train_test_split(X, Y, test_size = 0.1, random_state = 0)

    print(f'Running for {timer} mins')
    tpot = TPOTClassifier(generations=5, population_size=50, verbosity=10, max_time_mins = timer)
    tpot.fit(X_train, Y_train)

    acc = tpot.score(X_test, Y_test)
    print('################\n Accuracy Score: ', acc, '\n################')

    sys.stdout.close()
    #restore stdout
    sys.stdout = stdoutSave

    if not(os.path.exists(f'datasets/{folderName}')):
        os.mkdir(f'datasets/{folderName}') 

    from sklearn.externals import joblib
    joblib.dump(tpot.fitted_pipeline_, f'./datasets/{folderName}/pipeline.pkl')
    joblib.dump(le, f'./datasets/{folderName}/encoder.pkl')
    tpot.export(f'./datasets/{folderName}/pipeline.py')

    return acc

def predict_csv(folderName, target_col):
    from sklearn.externals import joblib
    from sklearn.preprocessing import LabelEncoder
    import pandas as pd
    
    try:
        pipeline = joblib.load(f'./datasets/{folderName}/pipeline.pkl')
        le = joblib.load(f'./datasets/{folderName}/encoder.pkl')

    except FileNotFoundError:
        return False

    # dataset must not have the predictive column
    df = pd.read_csv(f'./datasets/{folderName}/test.csv')
    
    le2 = LabelEncoder()
    X = df.apply(le2.fit_transform).values
    #print('DF: ',df.shape,'\tX: ',X.shape)

    pred = le.inverse_transform(pipeline.predict(X))

    df[f'{target_col} (Predicted)'] = pd.Series(pred, index = df.index)
    df.to_csv(f'./datasets/{folderName}/test_predicted.csv')

    return True