#!/bin/python3
import networkx as nx
import json
import sys
from os.path import dirname
#import matplotlib.pyplot as plt
from jinja2 import Template, Environment, FileSystemLoader

gate_type={}
input_array = []
output_array = []

CircuitGraph = nx.DiGraph()
CircuitGraph.add_node("In")
CircuitGraph.add_node("Out")

json_netlist = json.load(open(sys.argv[1], 'r'))["modules"]

for module_netlist in json_netlist.values():
    for port_json in module_netlist["ports"].values():
        if port_json["direction"] == "input":
            for bit in port_json["bits"]:
                CircuitGraph.add_edge("In",bit,weight = 0,type="input")
                input_array.append(bit)
        elif port_json["direction"] == "output":
            for bit in port_json["bits"]:
                CircuitGraph.add_edge(bit,"Out",weight = 0,type="output")
                output_array.append(bit)
        else:
            print("Port Definition Error")
            sys.exit(1)

    for cell_json in module_netlist["cells"].items():
        CircuitGraph.add_node(cell_json[0])
        gate_name = cell_json[1]["type"][2:-1]
        if gate_name == "ANDNOT":
            gate_name = "ANDYN"
        elif gate_name == "ORNOT":
            gate_name = "ORYN"
        gate_type[cell_json[0]] = gate_name

        for direction_json in cell_json[1]["port_directions"].items():
            if direction_json[1] == "input":
                CircuitGraph.add_edge(cell_json[1]["connections"][direction_json[0]][0],cell_json[0],weight = -1)
            elif direction_json[1] == "output":
                CircuitGraph.add_edge(cell_json[0],cell_json[1]["connections"][direction_json[0]][0],weight = 0)

            else:
                print("Cell Port Definition Error")
                sys.exit(1)

#print(list(nx.DiGraph.predecessors(CircuitGraph,"$abc$49$auto$blifparse.cc:371:parse_blif$50")))
#nx.draw(CircuitGraph,labels=gate_type)
#plt.show()

total_step = -nx.algorithms.shortest_paths.weighted.bellman_ford_path_length(CircuitGraph,"In","Out")
wire_set = set()
gate_array = [[] for i in range(total_step)]
#print(total_step)

for stage in dict(nx.algorithms.shortest_paths.weighted.single_source_bellman_ford_path_length(CircuitGraph,"In")).items():
    #print(stage)
    if type(stage[0]) is str and stage[0] != "In" and stage[0] != "Out":
        gate_array[-stage[1]-1].append(stage[0])
        if -stage[1] != total_step:
            wire_set.add(list(CircuitGraph.successors(stage[0]))[0])

wire_array = list(wire_set)

#print(input_array)
#print(output_array)
#print(wire_array)
#print(gate_array)
#print(gate_type)

template_array = [[] for i in range(total_step)]

for i in range(total_step):
    gate_stage = gate_array[i]
    for gate in gate_stage:
        result = ""
        ca = ""
        cb = ""

        wire = module_netlist["cells"][gate]["connections"]["Y"][0]
        if wire in output_array:
            result = "cipherout[" + str(output_array.index(wire)) + "]"
        else :
            result = "cipherwire["+ str(wire_array.index(wire)) + "]"

        wire = module_netlist["cells"][gate]["connections"]["A"][0]
        if wire in input_array:
            ca = "cipherin[" + str(input_array.index(wire)) + "]"
        else :
            ca = "cipherwire[" + str(wire_array.index(wire)) + "]"

        wire = module_netlist["cells"][gate]["connections"]["B"][0]
        if wire in input_array:
            cb = "cipherin["  + str(input_array.index(wire)) +"]"
        else :
            cb = "cipherwire[" + str(wire_array.index(wire)) + "]"

        template_array[i].append([gate_type[gate],result,ca,cb])

#print(template_array)

data ={"input_width":len(input_array), "output_width":len(output_array), "wire_max":len(wire_array), "template_array":template_array}
cloud_template_result = Environment(loader=FileSystemLoader('.')).get_template("cloud.cpp.template").render(data)
#print(str(cloud_template_result))
with open(dirname(sys.argv[1])+"/cloud.cpp","w") as f:
    f.write(cloud_template_result)