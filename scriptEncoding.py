from sklearn.preprocessing import LabelEncoder

def encodeCategoricalColumns(df, categories):
    d = {}
    for col in categories:
        le = LabelEncoder()
        df[col] = le.fit_transform(df[col])
        d[col] = le
        
    return d

def reEncodeCategoricalColumns(df, categories, encoders):
    for col in categories:
        df[col] = encoders[col].transform(df[col])

def decodeCategoricalColumns(df, categories, encoders):
    for col in categories:
        print(df[col].name, encoders[col].classes_)
        df[col] = encoders[col].inverse_transform(df[col])
        
def printEncoders(encoders):
    for key, val in encoders.items():
        print(key, val.classes_) 