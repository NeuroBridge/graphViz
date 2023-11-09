#!/usr/bin/env python 
import argparse
import csv
import operator
from py2cytoscape.data.cyrest_client import CyRestClient
import requests
import json
import time

# Here's the main entrypoint
parser = argparse.ArgumentParser()

# set up the arguement parsing and extract the args
parser.add_argument("--sifFile", help="sif formatted network file", required=True)
parser.add_argument("--targetNode", help="Node to show links for", required=False)
args = parser.parse_args()
sifFile = args.sifFile
targetNode = args.targetNode
targetNodeId = None
print(f"targetNode is {targetNode}")

# set up the network URL
cytoscape_url = "http://localhost:1234/v1"

# create the connection and the network
cy = CyRestClient()

# Start by deleting any existing networs
reply = requests.delete(f"{cytoscape_url}/networks/")
network = cy.network.create(name='NeuroBridge', collection='NeuroBridge collection')
network_collection_id = network.get_id()
print(f"network_collection_id is {network_collection_id}")

# create the basic network from the sifFile
NeuroNet = cy.network.create_from(sifFile)
print(f"NeuroNet is {NeuroNet}")

# Set up force directed network
cy.layout.apply(name='force-directed', network=NeuroNet)

# Create and apply a basic style
neuro_style =  cy.style.create('Neuro Style')

basic_settings = {
    # You can set default values as key-value pairs.
    'NODE_FILL_COLOR': '#6AACB8',
    'NODE_SIZE': 5,
    'NODE_BORDER_WIDTH': 0,
    'NODE_LABEL_COLOR': '#000000',
    'EDGE_WIDTH': 1,
    'EDGE_TRANSPARENCY': 100,
    'EDGE_STROKE_UNSELECTED_PAINT': '#333333',
    'NETWORK_BACKGROUND_PAINT': '#FFFFEA'
}

# 10 entry colormap
color_map_10 = [
   '#9E0142',
   '#D53E4F',
   '#F46D43',
   '#FDAE61',
   '#FEE08B',
   '#E6F598',
   '#ABDDA4',
   '#66C2A5',
   '#3288BD',
   '#5E4FA2'
]

# 6 entry colormap
color_map_6 = [
   '#D53E4F',
   '#FC8D59',
   '#FEE08B',
   '#E6F598',
   '#99D594',
   '#3288BD'
]
neuro_style.update_defaults(basic_settings)
cy.style.apply(neuro_style, NeuroNet)

networks_response = requests.get(f"{cytoscape_url}/networks")
networks_suid = networks_response.json()
print(f"networks_suid is {networks_suid}")

# We are deleting all of the networks at the start so this will be an array of
# two ints.  Whichever is not the network_collection_id is the one we want
if networks_suid[0] == network_collection_id:
   thisNetwork = networks_suid[1]
else: 
   thisNetwork = networks_suid[0]

print(f"thisNetwork is {thisNetwork}")

# We'll also need the network view
viewResponse = requests.get(f"{cytoscape_url}/networks/{thisNetwork}/views")
viewJSON = viewResponse.json()
viewSUID = viewJSON[0]
print(f"viewSUID is {viewSUID}")

# get the list of nodes
nodes_response = requests.get(f"{cytoscape_url}/networks/{thisNetwork}/nodes")
print (nodes_response)
nodes_data = nodes_response.json()
print(f"nodes_data is {nodes_data}")
print(len(nodes_data))
for node in nodes_data:
   nLinksUrl = f"{cytoscape_url}/networks/{thisNetwork}/nodes/{node}/adjEdges"
   list_of_links = requests.get(nLinksUrl)
   #print(f"list_of_links is {list_of_links.json()}")
   #print(f"nLinks is {len(list_of_links.json())}")

   node_data = requests.get(f"{cytoscape_url}/networks/{thisNetwork}/nodes/{node}")
   node_data = node_data.json()
   #print(f"node_data is {node_data}")
   nodeName = node_data['data']['name']
   nodeSUID = node_data['data']['SUID']
   print(f"nodeName, nodeSUID are {nodeName} {nodeSUID}")
   if nodeName == targetNode:
      targetNodeId = nodeSUID
      print(f"targetNodeId is {targetNodeId}")

   nodeNameProp = {
          'visualProperty': 'NODE_LABEL',
          'value': nodeName
    } 

   nodeFontProp = {
          'visualProperty': 'NODE_LABEL_FONT_SIZE',
          'value': 6
    } 

   putURL = f"{cytoscape_url}/networks/{thisNetwork}/views/{viewSUID}/nodes/{nodeSUID}?bypass=true"
   #print(f"putURL for nodes {putURL}")
   nodePropArray = []
   nodePropArray.append(nodeNameProp)
   nodePropArray.append(nodeFontProp)
   formattedProps = json.dumps(nodePropArray[0], indent = 3)
   #print(f"formattedProps {formattedProps}")
   reply = requests.put(putURL, json = nodePropArray)
   #print(f"node reply is {reply}")

# get the list of edges
edges_response = requests.get(f"{cytoscape_url}/networks/{thisNetwork}/edges")
print (edges_response)
edges_data = edges_response.json()
#print(f"edges_data is {edges_data}")
print(len(edges_data))

edge_thickness = {}
concept_list = {}
for edge in edges_data:
   edge_data = requests.get(f"{cytoscape_url}/networks/{thisNetwork}/edges/{edge}")
   edge_data = edge_data.json()
   #print(f"edges_data is {edge_data}")
   source = edge_data["data"]["source"]
   target = edge_data["data"]["target"]
   pair = (source, target)
   edge_thickness[pair] = edge_thickness.get(pair, 0) + .2
   #print(f"edge thickness of pair {source} {target} is {edge_thickness[pair]}")
   if pair not in concept_list:
      concept_list[pair] = []
#   print(f"appending concept {edge_data['data']['shared interaction']} for pair {source} {target}")
   concept_list[pair].append(edge_data["data"]["shared interaction"])

reply = requests.delete(f"{cytoscape_url}/networks/{thisNetwork}/edges/")
#print(f"delete reply is {reply}")

time.sleep(0.1)

for pair, thickness in edge_thickness.items():
    source, target = pair
    print(f"found {source} {target}")
    if targetNodeId != None and source != targetNodeId and target != targetNodeId:
       continue
    new_edge_array = []
    new_edge_data = {
        "source": source,
        "target": target,
    }
    new_edge_array.append(new_edge_data)

    # Add the new edge to the network
    reply = requests.post(f"{cytoscape_url}/networks/{thisNetwork}/edges", json = new_edge_array)
    #print(f"repost reply is {reply}")
    replyJSON = reply.json()
    #print(f"repost replyJSON is {replyJSON }")
    #print(f"thickness is {thickness }")

    visualProp = {
          "visualProperty": "EDGE_WIDTH",
          "value": thickness
    } 

    visualFontProp = {
          'visualProperty': 'EDGE_LABEL_FONT_SIZE',
          'value': 2
    } 


    visualPropArray = []
    visualPropArray.append(visualProp)
    visualPropArray.append(visualFontProp)

    conceptArray = concept_list[pair]
    conceptString = "\n".join([str(item) for item in conceptArray])
    conceptProp = {
          "visualProperty": "EDGE_TOOLTIP",
          "value": conceptString
    }
    visualPropArray.append(conceptProp)
  
    edgeSUID = replyJSON[0]['SUID']
    putURL = f"{cytoscape_url}/networks/{thisNetwork}/views/{viewSUID}/edges/{edgeSUID}"
    #print(f"putURL {putURL}")
    formattedProps = json.dumps(visualPropArray[0], indent = 3)
   # print(f"formattedProps {formattedProps}")

    reply = requests.put(putURL, json = visualPropArray)
    #print(f"visualProp reply is {reply}")
    time.sleep(0.05)
