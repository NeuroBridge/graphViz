#!/usr/bin/env python 
import argparse
import csv
import operator
from py2cytoscape.data.cyrest_client import CyRestClient
import requests
import json

# Here's the main entrypoint
parser = argparse.ArgumentParser()

# set up the arguement parsing and extract the args
parser.add_argument("--sifFile", help="sif formatted network file", required=True)
args = parser.parse_args()
sifFile = args.sifFile

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
    'NODE_LABEL_COLOR': '#555555',
    'EDGE_WIDTH': 1,
    'EDGE_TRANSPARENCY': 100,
    'EDGE_STROKE_UNSELECTED_PAINT': '#333333',
    'NETWORK_BACKGROUND_PAINT': '#FFFFEA'
}
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

# get the list of edges
edges_response = requests.get(f"{cytoscape_url}/networks/{thisNetwork}/edges")
print (edges_response)
edges_data = edges_response.json()
print(f"edges_data is {edges_data}")
print(len(edges_data))

edge_thickness = {}
concept_list = {}
for edge in edges_data:
   edge_data = requests.get(f"{cytoscape_url}/networks/{thisNetwork}/edges/{edge}")
   edge_data = edge_data.json()
   print(f"edges_data is {edge_data}")
   source = edge_data["data"]["source"]
   target = edge_data["data"]["target"]
   pair = (source, target)
   edge_thickness[pair] = edge_thickness.get(pair, 0) + .5
   print(f"edge thickness of pair {source} {target} is {edge_thickness[pair]}")
   if pair not in concept_list:
      concept_list[pair] = []
   print(f"appending concept {edge_data['data']['shared interaction']} for pair {source} {target}")
   concept_list[pair].append(edge_data["data"]["shared interaction"])

reply = requests.delete(f"{cytoscape_url}/networks/{thisNetwork}/edges/")
print(f"delete reply is {reply}")

for pair, thickness in edge_thickness.items():
    source, target = pair
    #print(f"found {source} {target}")
    new_edge_array = []
    new_edge_data = {
        "source": source,
        "target": target,
    }
    new_edge_array.append(new_edge_data)

    # Remove existing multiple edges (if any) between source and target
 #   reply = requests.delete(f"{cytoscape_url}/networks/{thisNetwork}/edges/{source},{target}")
  #  print(f"delete reply is {reply}")

    # Add the new edge to the network
    reply = requests.post(f"{cytoscape_url}/networks/{thisNetwork}/edges", json = new_edge_array)
    #print(f"repost reply is {reply}")
    replyJSON = reply.json()
    #print(f"repost replyJSON is {replyJSON }")
    print(f"thickness is {thickness }")

    visualProp = {
          "visualProperty": "EDGE_WIDTH",
          "value": thickness
          #"value": 20
    } 

    visualPropArray = []
    visualPropArray.append(visualProp)

    conceptArray = concept_list[pair]
    conceptString = "\n".join([str(item) for item in conceptArray])
    conceptProp = {
          "visualProperty": "EDGE_LABEL",
          "value": conceptString
    }
    rotateProp = {
          "visualProperty": "EDGE_LABEL_AUTOROTATE",
          "value": True
    }
    sizeProp = {
          "visualProperty": "EDGE_LABEL_FONT_SIZE",
          "value": 2
    }
    visualPropArray.append(conceptProp)
    visualPropArray.append(rotateProp)
    visualPropArray.append(sizeProp)
  
    edgeSUID = replyJSON[0]['SUID']
    putURL = f"{cytoscape_url}/networks/{thisNetwork}/views/{viewSUID}/edges/{edgeSUID}"
    print(f"putURL {putURL}")
    formattedProps = json.dumps(visualPropArray[0], indent = 3)
    print(f"formattedProps {formattedProps}")

    reply = requests.put(putURL, json = visualPropArray)
    #print(f"thickness reply is {reply}")
