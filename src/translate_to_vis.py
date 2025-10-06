import os
import numpy as np
import typer
import json
import jsonlines



CUR_DIR = os.path.dirname(os.path.abspath(__name__))
VIS_JS_FORMAT_NODE = '''{id: %d, label: "%s", color: {background: '%s'}}'''
VIS_JS_FORMAT_LINK = '''{from: %d, to: %d, label: "%s", color: {color: '%s', highlight: '%s'}, font: { size: 18 }, arrows: { to: { enabled: true, type: 'arrow'}}}'''


# TODO: highlight color and border can be changed too.
# color: {
#       border: '#2B7CE9',
#       background: '#97C2FC',
#       highlight: {
#         border: '#2B7CE9',
#         background: '#D2E5FF'
#       },


NODE_COLORS = {'being': '#279aba', 'action_choice': '#ba2769', 'event': '#e6c440','value': '#8e7db5'}
LINK_COLORS = {'1': '#b518a8', '2': '#f540e6'}

HEADER = "<html>\n<head>\n<script type='text/javascript'\
src='https://unpkg.com/vis-network/standalone/umd/vis-network.min.js'></script>\
    \n<style type='text/css'>\
      \n #mynetwork {\
        \n\t\twidth: %dpx;\
         \n\t\theight: %dpx;\
         \n\t\tborder: 1px solid lightgray;\
       \n\t }\
   \n\t </style>\
\n</head>\
\n<body>\
\n<div id='mynetwork'></div>\n"
    

BODY = '\n<script type="text/javascript">\
    \n\nwindow.onload = function(){\
       \n\tlaunch_visualization()\
    \n}\
    \nfunction launch_visualization() { \
        \n\tthis_dset =  return_vis_dataset()\
        \n\tnodes = this_dset[1]\
        \n\tedges = this_dset[0]\
        \n\t// create a network\
        \n\tvar container = document.getElementById("mynetwork");\
        \n\tvar data = {\
            \n\t\tnodes: nodes,\
            \n\t\t edges: edges\
         \n\t\t};\
    \n\tvar options = {\
		\n\t\tphysics: {\
			\n\t\t\tenabled: true,\
			\n\t\t\tbarnesHut: {\
			\n\t\t\ttheta: 0.5,\
			\n\t\t\tgravitationalConstant: -5000,\
			\n\t\t\tspringLength: 500,\
			\n\t\t\tspringConstant: 0.01,\
			\n\t\t\tdamping: 5,\
			\n\t\t\tavoidOverlap: 1\
			\n\t\t}\
		\n\t},\
		\n\t\tmanipulation: {\
			\n\t\t\tenabled: true,\
			\n\t\t\tinitiallyActive: false,\
			\n\t\t\taddNode: true,\
			\n\t\t\taddEdge: true,\
			\n\t\t\teditEdge: true,\
			\n\t\t\tdeleteNode: true,\
			\n\t\t\tdeleteEdge: true,\
		\n\t\t\t},\
		\n\t\tnodes: {\
			\n\t\t\tshape: "circle",\
            \n\t\t\tfont: { size: 16 },\
            \n\t\t\t},\
         \n\t\tedges: {\
         \n\t\t\tlength: 2000,\
         \n\t\t},\
	}; \
       \n // initialize your network!\
         \n\tvar network = new vis.Network(container, data, options);\
    \n}\n'
    

CODA = '\n</script>\
\n</body>\
\n</html>'


def wrap_text(txt,width=5):
    txt_split =  txt.split(' ')
    txt_wrapped = [(" ".join(txt_split[i:i+width])) for i in range(0, len(txt_split), width)]
    txt_complete = "\\n ".join(txt_wrapped)
    # print(txt_complete)
    return (txt_complete)


def main(json_file: str = typer.Option(None, help="name of json file to use")):

    # define reader 
    print(json_file)
    reader = jsonlines.open(json_file, 'r')

    # get every node from the input file and store in list
    node_list = list(reader)

    #graph size
    n_nodes = len(node_list)

    width = n_nodes * 120
    height = n_nodes * 120

    # define output file
    output_file = open(json_file.split('.json')[0]+'.html','w')    

    #write and fill in header
    output_file.write(HEADER % (width, height))
    output_file.write(BODY)

    # define initial function and variable in the output file
    output_file.write("""function return_vis_dataset() {\n\tvar nodes = new vis.DataSet([ \n\t\t""")
    

    # iterate through nodes and write them to node datastructure in js file    
    
    # create list of nodes from node list
    node_labs_list = {}

    for ind,item in enumerate(node_list):                
        
        this_lab = item['node']['label']
        this_node_kind = item['node']['kind']

        try:
            this_color = NODE_COLORS[this_node_kind]
        except:
            this_color = '#62a3a2'

        this_lab_wrapped = wrap_text(this_lab)
        this_line = VIS_JS_FORMAT_NODE % (ind+1, this_lab_wrapped,this_color)
       
        node_labs_list[this_lab] = ind

        if(ind<(len(node_list)-1)):
            this_line=this_line+',\n\t\t'
        else:
            this_line=this_line+'\n\t\t]);'
       
        output_file.write(this_line)
    
    
    output_file.write('\n\tvar edges = new vis.DataSet([ \n\t\t')

    
    # create list of edges for each node
    # loop through each node and write out each of its links!
    for node_ind,item in enumerate(node_list):        

        
        this_node_lab = item['node']['label']
        these_links = item['links']    
        this_node_kind = item['node']['kind']

        if(this_node_kind=='action_choice'):
            this_color_1 = LINK_COLORS['1']
            this_color_2 = LINK_COLORS['2']
            
        else:
            this_color_1 = '#62a3a2'
            this_color_2 = LINK_COLORS['2']


        is_last_node = node_ind==(len(node_list)-1)      
        is_first_node = node_ind==0

        #decide if we will close this list or not.. 
        if(is_last_node and len(these_links)==0):
            output_file.write(']);\n')
        # elif(is_first_node==False and len(these_links)>0):
        #     output_file.write('\n\t\t')

        for link_ind,link in enumerate(these_links):

            # link_lab  = link['link']['kind']+"_"+link['link']['value']
            link_lab = link['link']['value']
            from_node = node_ind+1
            to_node = node_labs_list[link['to_node']]+1
            this_line = VIS_JS_FORMAT_LINK % (from_node, to_node, link_lab, this_color_1, this_color_2)       

            #add a comma only if there are more links to list
            if(link_ind<len(these_links)):
                this_line=this_line+',\n\t\t'
            if(is_last_node and link_ind==len(these_links)-1):
                this_line=this_line+']);\n'
                # print('closing node list')

            output_file.write(this_line)

    output_file.write('\n\treturn ([edges,nodes])')
    output_file.write('''\n}''')

    output_file.write(CODA)                      
    output_file.close()



	# // TODO: define methods that selectively hide or remove certain elements... still working on this
	# // need to find way to select by label or find a way to tag nodes
	# // // Get all edges
	# // var sN = network.selectNodes([1,2])
	# // var allEdges = network.getSelectedNodes(sN)
	# // network.deleteSelected()
	# // // network.
	# // // getEdges();

	# // // Log the edges to the console
	# // console.log(allEdges);