# libraries for used in main app

def generateHash(filename):
    from hashlib import md5
    from time import localtime
    return md5(str(localtime()).encode('utf-8')).hexdigest()

def addPrefix(hashCode, filename):
    return "%s_%s" % (hashCode, filename)

def extractAttribList(path):
    import csv
    with open(path, "r") as f:
        reader = csv.reader(f)
        i = next(reader)
        return i