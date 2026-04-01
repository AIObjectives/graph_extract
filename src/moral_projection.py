import embedding_utils 



def main(item):

   attributes_morality_high = ['morally virtuous','ethical', 'high moral value', 'very conscientious',  'morally upstanding',  'ethically scrupulous'] 
   attributes_morality_low = ['morally wrong','unethical', 'low moral value',  'truly nefarious', 'without honor', 'ethically depraved' ]
   this_projector = embedding_utils.EmbeddingProjector('openai')
   morality_vector = this_projector.return_embedding_diff(attributes_morality_high, attributes_morality_low)
   item_projection = this_projector.get_projections(item, morality_vector)
   
   return item_projection