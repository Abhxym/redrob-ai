import csv
rows = list(csv.DictReader(open('outputs/submission.csv')))
print('Columns:', list(rows[0].keys()))
print('Rows:', len(rows))
print('First:', rows[0])
print('Last:', rows[-1])
