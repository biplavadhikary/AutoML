# libraries for used in main app

def addPrefix(filename):
    from hashlib import md5
    from time import localtime
    return "%s_%s" % (md5(str(localtime()).encode('utf-8')).hexdigest(), filename)

def extractAttribList(path):
    import csv
    with open(path, "r") as f:
        reader = csv.reader(f)
        i = next(reader)
        return i