#!/usr/bin/env python 
import argparse
import csv
from pyvis.network import Network
from IPython.core.display import display, HTML

parser = argparse.ArgumentParser()
print (parser.prog)

parser.add_argument("--pmcfile", help="File with PMCS and terms", required=True)
parser.add_argument("--output", help="output file", required=True)
args = parser.parse_args()
pmcfile = args.pmcfile
output = args.output

# create the network we need
net = Network('1500px', '1500px')
idCounter = 1

with open(pmcfile, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    for row in reader:
        net.add_node(idCounter, label = row[0])
        idCounter = idCounter + 1
        print (row[0])
        print(', '.join(row))

net.show(output, notebook=False)        
