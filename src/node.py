
# eventually nodes can be typed, inherit from node class but be distinctly Being, Action Choice, or Event.
class Node():

  def __init__ (self,label,kind):
    self.label = label
    self.kind = kind #can be: being, action choice, event.
    self.links = list()

  def link_link(self,a_link,a_node):
    x = (a_link,a_node)
    self.links.append(x)

  def print(self):

    return ({"kind": self.kind, "label": self.label})

  def print_all(self):

    link_list = []

    for l in self.links:
      link_list.append({'link': l[0].print(), 'to_node': l[1].print()['label']})

    node_dict = {'node': self.print(), 'links': link_list}

    return node_dict

class Link():

    def __init__(self,kind,value):
      self.kind = kind
      self.value = value
      # self.label = label

    def print(self):
      return ({"kind": self.kind, "value": self.value})

class Graph():

  def __init__(self):        
    self.nodes = [];
    self.links = [];


  def add_node(self,node):
    self.nodes.append(node)
    return(node)

  def add_link(self, link):
    self.links.append(link)
    return(link)

  def print_graph(self):
   return ([n.print_all() for n in self.nodes])


  def return_node(self,label):
    #finds node with a label and returns pointer to it
    nodes_with_label = [n for n in self.nodes if n.label == label]
    return(nodes_with_label)


  def list_nodes(self):
    print([n.label+'\n' for n in self.nodes])


  def reset(self):
    self.nodes = [];
    self.links = [];

