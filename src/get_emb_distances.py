

import os
import json, jsonlines
import pandas as pd
from dotenv import dotenv_values
from dotenv import load_dotenv
import requests
import numpy as np
from scipy.spatial.distance import cdist
import random
import typer


# set some global variables
load_dotenv() 
global config
config = dotenv_values(".env")

# set current path
CUR_DIR = os.path.dirname(os.path.abspath(__name__))

class Embedding():
    def __init__ (self,items,attr_list_1 = [], attr_list_2 = [], model_name = "text-embedding-ada-002"):
       self.model_name = model_name
       self.items = items
       self.attr_list_1 = attr_list_1
       self.attr_list_2 = attr_list_2
       self.attr_vector_emb = []
       self.item_attr_projections = []
       self.item_embs = []
       
    def get_embedding(self,text):
        url = 'https://api.openai.com/v1/embeddings'
        headers = {
        "Content-Type": "application/json",
        "Authorization": config['OPENAI_API_KEY']
        }
        data = { 
            "input": text,
            "model": self.model_name
        }
        response = requests.post(url, headers=headers, json=data)
        
        return response.json()


    def get_attribute_vector(self):
        emb_high = pd.DataFrame()
        emb_low = pd.DataFrame()

        list1 = self.attr_list_1
        list2 = self.attr_list_2

        #loop through each attribute set and save the embeddings in two dataframes
        for a in range(len(list1)):
            #get embedding of the high, low, and compute difference
            this_emb = self.get_embedding(list1[a])
            emb_high.insert(loc=0,column=a,value=this_emb["data"][0]["embedding"])

        for b in range(len(list2)):
            #get embedding of the high, low, and compute difference
            this_emb = self.get_embedding(list2[b])
            emb_low.insert(loc=0,column=b,value=this_emb["data"][0]["embedding"])

        #get all differences
        vector_diff = pd.DataFrame()

        for a in range(len(list1)):
            for b in range(len(list2)):
                this_col = str(a)+'_'+str(b)
                vector_diff.insert(loc=0,column = this_col, value = emb_high[a] - emb_low[b])
            
        self.attr_vector_emb = vector_diff.mean(axis=1)
        

    def get_list_embeddings(self):
       
       item_embs = [self.get_embedding(i)["data"][0]["embedding"] for i in self.items]
       self.item_embs = item_embs

       return item_embs


    def get_projections(self):
   
        item_list = self.items    #list of items 
        self.get_attribute_vector()   #obtain attribute projections for those items
        attr_emb =  self.attr_vector_emb 
    
        assert(len(attr_emb)>0)
        assert(len(item_list)>0)

        item_projections = {}

        for item in item_list:
            # get embedding of item
            item_emb = self.get_embedding(item)["data"][0]["embedding"]
            # project it onto the attribute vector
            projection_attr = np.inner(np.array(item_emb),np.array(attr_emb))
            item_projections[item] = projection_attr

        self.item_attr_projections = item_projections
    

def threshold_by_sim(item_list,threshold):


    # create a new Embeddings object
    E = Embedding(item_list)

    emb_list = [E.get_embedding(x)['data'] for x in item_list]
    emb_vectors = [np.array(x[0]['embedding']) for x in emb_list]
    emb_array=np.array(emb_vectors)
    
    #create distance matrix on pure embeddings 
    n_item = len(item_list)
    emb_distance = np.full((n_item,n_item),np.nan)                               


    for i in range(len(emb_array)):
        for j in range(i + 1, len(emb_array)):

            ag1=np.reshape(emb_array[i],(1,len(emb_array[i])))
            ag2=np.reshape(emb_array[j],(1,len(emb_array[j])))
            emb_distance[i,j] = cdist(ag1, ag2,'cosine')[0][0]

    assert(emb_distance.shape == (n_item,n_item))

    indices = np.where((emb_distance < threshold) & (emb_distance != np.nan ))
    close_pairs = [(item_list[x], item_list[y]) for (x,y) in zip(indices[0],indices[1])]
    close_pairs
    
    #now collapse the items that were synonyms (in close items)
    return_list = item_list

    for pair in close_pairs:      

        #just pick one of the two for now
       rm_item = random.choice(pair)
       try:
           return_list.remove(rm_item)
       except:
           pass

    return return_list