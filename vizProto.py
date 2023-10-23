#!/usr/bin/env python 
import argparse
import csv
from pyvis.network import Network
from IPython.core.display import display, HTML
from ordered_set import OrderedSet

class Edge:
     def __init__(self, node1, node2, concept):
         self.node1 = node1
         self.node2 = node2
         self.node_key1 = f"{node1}-{node2}"
         self.node_key2 = f"{node2}-{node1}"
         self.conceptArray = []
         self.conceptArray.append(concept)

     def matchEdge(self, node1, node2):
       node_key = f"{node1}-{node2}"
       if (node_key == self.node_key1 or node_key == self.node_key2):
          return True
       else:
          return False

# Function to search an array of Edge classes, to see if thisEdge is there
def findPriorEdge(edgeData, thisEdge):
   for edgeToCompare in edgeData:
     if edgeToCompare.matchEdge(thisEdge.node1, thisEdge.node2):
        # found one.
        return edgeToCompare

   # Didn't find a priorEdge
   return None

def createRenderedEdgeList(data, net, edgeList):

   # Important: This array of edge is an array of distinct edges. If two studies are connected   
   # by more than one concept we still only want one edge on the graph because it's too busy to be
   # useful
   edgeData = []

   # Not the most elegant way to do this, but it does work
   # Do an embedded loop through the data to make a list of all
   # of linked nodes
   for  array1 in data:
      id1 = array1[0]
      node1 = array1[1]
      concept1 = array1[2]
      print (f"array1 {id1} {node1} {concept1} ")
      for array2 in data:
        id2 = array2[0]
        node2 = array2[1]
        concept2 = array2[2]
        print (f"array2 {id2} {node2} {concept2} ")
        if concept1 == concept2 and node1 != node2:
          # The concepts are the same and the nodes are different.
          # So we need to link these.
          print (f"{node1} and {node2} are linked by {concept1} ")

          # Create an edge object for this link
          thisEdge = Edge(id1, id2, concept1)

          # Is there an existing link between these 2 nodes?
          priorEdge = findPriorEdge(edgeData, thisEdge)
          if (priorEdge == None):
             # No existing edge, add the edge array (the edges that will be rendered)
             edgeData.append(thisEdge)
          else:
             # Yes there is an existing edge. Let's add the current concept to the 
             # array of concepts linking these 2 nodes.
             print(f"found an existing edge for {concept1}")
             priorEdge.conceptArray.append(concept1)
         
   # Add the edges to be rendered to the concept list for the edge 
   print (f"number of edges is {len(edgeData)}")
   for edgeToAdd in edgeData:
     net.add_edge(edgeToAdd.node1, edgeToAdd.node2, title=edgeToAdd.conceptArray[0], physics=False)


# Here's the main entrypoint
parser = argparse.ArgumentParser()

# set up the arguement parsing and extract the args
parser.add_argument("--pmcfile", help="File with PMCS and terms", required=True)
parser.add_argument("--output", help="output file", required=True)
args = parser.parse_args()
pmcfile = args.pmcfile
output = args.output

# create the network we need
net = Network('1500px', '1500px')
idCounter = 1
nodeSet = set()
edgeList = []
data = []

# open the CSV file
with open(pmcfile, newline='') as csvfile:
    reader = csv.reader(csvfile, delimiter=',', quotechar='|')
    # skip the header line
    next(reader)

    for row in reader:
        thisLabel = row[0]
        thisConcept = row[1]
        
        # Have we already seen this node/study in the file?
        if thisLabel not in nodeSet:
           # nope we need to add it. 
           net.add_node(idCounter, label = thisLabel, title=thisLabel)
           thisDataArray = [idCounter, thisLabel, thisConcept]
           print (f"adding data {idCounter} {thisLabel} {thisConcept} ")
           #thisData = OrderedSet(thisDataArray)
           # Add this node to the array of data we need for createRenderedEdgeList
           data.append(thisDataArray)

           nodeSet.add(thisLabel)
           idCounter = idCounter + 1

# create the list of edges to render and add them to the net.
createRenderedEdgeList(data, net, edgeList)


print (idCounter)
net.show(output, notebook=False)        
