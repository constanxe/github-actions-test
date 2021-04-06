import csv

def readCSVFromLoyalty(contents, loyalty_id):
    reader = csv.reader(contents.split('\r\n'))
    if loyalty_id == "EMINENT":
        return csv_process_eminent(reader)
    elif loyalty_id == "CONRAD":
        return csv_process_conrad(reader)
    elif loyalty_id == "QUANTUM":
        return csv_process_quantum(reader)
    else:
        return csv_process_default(reader)


# Adapter #

# 0, 1, 2, 3 --> 0, 1, 2, 3
def csv_process_default(reader):
    transactions = []
    header = next(reader)
    for row in reader:
        transactions.append(row)
    
    return header, transactions

# 0, 2, 1, 3 --> 0, 1, 2, 3
def csv_process_conrad(reader):
    transactions = []
    header = next(reader)
    for row in reader:
        row[1], row[2] = row[2], row[1]
        transactions.append(row)
    
    return header, transactions

# 3, 2, 1, 0 --> 0, 1, 2, 3
def csv_process_eminent(reader):
    transactions = []
    header = next(reader)
    for row in reader:
        row[3], row[2], row[1], row[0] = row[0], row[1], row[2], row[3]
        transactions.append(row)
    
    return header, transactions

# 3, 1, 2, 0 --> 0, 1, 2, 3
def csv_process_quantum(reader):
    transactions = []
    header = next(reader)
    for row in reader:
        row[3], row[0] = row[0], row[3]
        transactions.append(row)
    
    return header, transactions