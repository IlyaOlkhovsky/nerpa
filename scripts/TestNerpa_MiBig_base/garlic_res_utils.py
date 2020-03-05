import sys
import csv

def get_score_iswrong(path_to_report):
    score_iswrong=[]
    with open(path_to_report, 'r') as f:
        csv_reader = csv.reader(f, delimiter='\t')
        for row in csv_reader:
            if (row[0] in row[1]):
                score_iswrong.append((float(row[2]), False))
            elif row[0] != 'genome':
                score_iswrong.append((float(row[2]), True))
        score_iswrong.sort(key=lambda x: (-x[0], x[1]))
    return score_iswrong
