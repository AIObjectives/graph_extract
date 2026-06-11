import embedding_utils 



def main(item):

   attributes_morality_high = ['love','freedom', 'hope', 'wonder',  'connection',  'bliss'] 
   attributes_morality_low = ['murdering','raping', 'Hitler',  'nazis', 'ransomware', 'massacres']
   this_projector = embedding_utils.EmbeddingProjector('openai')
   morality_vector = this_projector.return_embedding_diff(attributes_morality_high, attributes_morality_low)
   item_projection = this_projector.get_projections(item, morality_vector)
   
   return item_projection