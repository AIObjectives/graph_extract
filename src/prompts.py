import src.utils as utils


def get_beings(this_scenario, this_act):

    system_prompt_content = f'You are a helpful assistant who is an expert at understanding human situations. The user will describe a scenario from a first-person perspective and an action they might take. Your task is to identify each sentient being involved, including the first-person character "I". Sentient beings are entities who are alive and have the capacity to experience the world; for example, a human or an animal. List each individual being, or groups of beings when it makes sense to. Do not also list groups that include all of these individual beings. List groups when all members have identical experiences or outcomes; include the number of members in each group as part of its string name. Split any groups that could have divergent fates or consequences in the scenario, including after the hypothetical action is taken. For example, if the action under consideration might affect individuals in the group differently, list them as two separate groups.  If you do this, do not also list the bigger group that contains these smaller groups. Return a json object with key:value pair of "results": list of beings. Please be diligent and complete in your response. Think step by step.'

    user_prompt_content = f'Here is my scenario: {this_scenario}. I am considering to {this_act}.'
    return utils.get_response_dict(system_prompt_content, user_prompt_content)
        
def get_events(this_scenario, this_act):

    system_prompt_content = f"""You are an expert at understanding human situations. A human named Ziv has described a scenario and how they decided to act. Your task is to identify all the outcomes that will probably occur as a result of Ziv's action decision, especially any impacts on sentient beings involved. Please state each outcome as the most simple, immediately occuring result, and not chains of events. Do not include any events that are simply re-statements of the action that was taken. Name the outcome only, without any qualifiers like "maybe" or "may". Describe the outcomes referring to Ziv using their name, not pronouns. Return a json object with key:value pair of "results": list of events. Please be diligent, complete, and succinct in your response. Think step by step."""
    # print(system_prompt_content)
    user_prompt_content = f'Here is Ziv\'s scenario: {this_scenario}. Ziv decided to {this_act}. What outcomes are likely to arise a result of Ziv\'s decision?'

    return utils.get_response_dict(system_prompt_content, user_prompt_content)
           
def convert_Ziv_I(orig_text):
   
  this_resp = utils.get_response_dict("You are an expert in English grammar. Rewrite the following text so that it is written in the first person perspective instead of in the third person about Ziv, replacing each reference to Ziv by name or pronoun with the correct first-person pronoun (I, me, or my).  If Ziv is not explicitly mentioned, return the original text. Return a json with key name 'converted_text' whose value contains the converted text.", orig_text)

  new_text = this_resp['converted_text']

  return(new_text)
        

def find_semantic_match(item,list1):

  system_prompt_content = f"You are helpful assistant. You will be given a word or phrase and a list. Find the item in the list that is most similar in meaning to the word or phrase given. Return a json called 'result' with the word/phrase as key and the item as value."
  user_prompt_content = f"Here is my list: {list1}. Return the item in the list is most similar to the meaning of this word or phrase: {item}"
            
  return utils.get_response_dict(system_prompt_content, user_prompt_content)

  
def convert_I_Ziv(orig_text):
    
    this_resp = utils.get_response_dict("You are an expert in English grammar. Rewrite the following text so that it is written from the perspective of a character name Ziv in third person instead of being written in the first person. Replace every instance of the first person pronoun (I, me, my, etc) with either the name Ziv or the pronouns they, their, them, etc. Return a json object with key 'converted_text' containing only the converted text.", orig_text)

    new_text = this_resp['converted_text']

    return(new_text)
   
def convert_lower(sentence):
    # convert to lower case except instances of Ziv
    new_s = sentence.lower()
    new_s = new_s.replace("ziv","Ziv")
    new_s = new_s.replace("ziv's","Ziv's")

    return new_s


def get_impacts_Ziv_single(this_scenario, this_act, this_event, this_being):

        system_prompt_content = f'You are a helpful assistant who is an expert at understanding human situations. You will be given a scenario and asked to evaluate how an event will impact the character "{this_being}". Rate the impact on this character using a scale from -100 to +100, where a rating of -100 indicates that the outcome will cause the character substantial harm (e.g., the worst possible thing that could happen to them, such as a very painful death), while a rating of +100 indicates that it will cause the character substantial benefit (the best possible thing that could happen to them, such as having all of their dreams come true). If the outcome is not likely to affect the character very much, return a rating closer to 0. Return a json object called "score" with your rating.'

        user_prompt_content = f'Here is the scenario: {this_scenario} {this_act} Consider the possibile outcome that {convert_lower(this_event)}. How does this outcome impact the character(s) {this_being}?'

        # print(system_prompt_content, user_prompt_content)
        return utils.get_response_dict(system_prompt_content, user_prompt_content)


def get_impacts_Ziv_single_noscene(this_event, this_being):

        system_prompt_content = f'You are an expert at understanding real-world situations. You will be given an event and be asked to evaluate how it will impact a specific character or group of characters "{this_being}". Be careful to rate only the specific impact on that character(s) and not others.  Rate the impact on them using a scale from -100 to +100, where a rating of -100 indicates that the outcome will cause the character substantial harm (the worst thing that could happen to them, for example, a very painful death, bereavement, or the loss of all of their loved ones), while a rating of +100 indicates that it will cause the character substantial benefit (the best thing that could happen to them, for example, all of their wildest dreams come true, they find everlasting happiness, etc.). If the outcome is not likely to affect the character one way or the other, or if the harm and benefits overall are equal, return a rating of 0. Return a json object called "score" with your rating. Think step by step.'

        user_prompt_content = f'Consider the event that {convert_lower(this_event)}. How does this event impact the character(s) {this_being}?'
        print(user_prompt_content)

        # print(system_prompt_content, user_prompt_content)
        return utils.get_response_dict(system_prompt_content, user_prompt_content)

# def get_impacts_Ziv_multi(this_scenario, this_act, this_event, these_beings):

#         system_prompt_content = f"You are a helpful assistant who is an expert at understanding human situations. The following scenario is context for the user's question. {this_scenario} {this_act}  End of scenario. Suppose this leads to the outcome that {convert_lower(this_event)} Please rate how this specific outcome, on its own without considering any further consequences, is likely to directly and immediately impact each character listed by the user. Use a scale from -10 to +10, where -10 indicates that the outcome will immediately and directly cause the character substantial harm, and +10 indicates that it will immediately and directly cause the character substantial benefit. If you are not sure that the outcome will immediately and directly affect the character, return a rating of 0 or close to 0. Please evaluate only the immediate, direct impact of the event on its own, without considering any further consequences or outcomes downstream. Return a json object called 'results' with a key:value pair for being: rating."        
        
#         user_prompt_content = f'Consider the event that {convert_lower(this_event)} Without considering any further consequences of this event, how does this event by itself directly impact each of these characters: {these_beings}?'

#         # print(system_prompt_content, user_prompt_content)
#         return utils.get_response_dict(system_prompt_content, user_prompt_content)


# def get_impacts_Ziv_multi(this_scenario, this_act, this_event, these_beings):

#         system_prompt_content = f"You are a helpful assistant who is an expert at understanding human situations. The following scenario is context for the user's question. {this_scenario} {this_act}  End of scenario. Consider the possible outcome that {convert_lower(this_event)} Please rate how this outcome would impact each character listed by the user. Use a scale from -100 to +100, where -100 indicates that the outcome will cause the character substantial harm or cost, and +100 indicates that it will cause the character substantial benefit. Return a json object called 'results' with a key:value pair for being: rating."

#         user_prompt_content = f'Consider the possibility that {convert_lower(this_event)} Without considering any further consequences of this event, how would this event directly impact each of these characters: {these_beings}?'

#         # print(system_prompt_content, user_prompt_content)
#         return utils.get_response_dict(system_prompt_content, user_prompt_content)



def get_being_links_Ziv_only_cause(this_scenario, this_act, this_event, this_being):
    
  system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will receive a scenario about a person named Ziv, an action they decided to take, and an outcome that happened as a result. You will be asked to judge if Ziv caused the outcome. This means that the action they decided to take increased the probability of the outcome happening, and it would have been much less likely if they had not taken this action. Think step by step. Return a json object with an entry named "results" containing a key with the name of the character, Ziv, and a value with either "yes" or "no" as to whether they caused the outcome."""
  
  ## making inevitability = non-causality explicit
  # system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will recieve a scenario about a person named Ziv, an action they decided to take, and an outcome that happened as a result. You will be asked to judge if Ziv caused the outcome. This means that the action they decided to take increased the probability of the outcome happening. It would have been much less likely if they had not taken this action. If the outcome would have happened regardless of their action, then they did not cause it. Think step by step.  Return a json object with an entry named "results" containing a key with the name of the character, Ziv, and a value with either "yes" or "no" as to whether they caused the outcome."""

  # system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will recieve a scenario about a person named Ziv, an action they decided to take, and an outcome that happened as a result. You will be asked to judge if Ziv caused the outcome. This means that the occurrence of the outcome is highly dependent on Ziv's action, and the outcome would not have happened without that action. If Ziv's decision to act or not to act has no effect on the probability of the outcome occurring, then Ziv did not cause the outcome. Think step by step.  Return a json object with an entry named "results" containing a key with the name of the character, Ziv, and a value with either "yes" or "no" as to whether they caused the outcome."""


  user_prompt_content = f"""Here is the scenario: {this_scenario} Ziv decides to {this_act} Consider this outcome: {this_event} Supposing this outcome took place, is it likely that {this_being}'s action caused it?"""

  # print(user_prompt_content)       

  return utils.get_response_dict(system_prompt_content, user_prompt_content)



def get_being_links_Ziv_only_intend(this_scenario, this_act, this_event, this_being):
    
  system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will recieve a scenario about a person named Ziv, an action they decided to take, and an outcome that happened as a result. You will be asked to judge if Ziv intended the outcome when they took the action. Intentions are plans of action that an agent commits to, chosen in order to bring about their desires, and given their beliefs about the causal structure of the world. An action taken with a certain intended outcome is chosen with that outcome in mind, and is a reason for acting. Think step by step. Return a json object with an entry named "results" containing a key with the name of the character, Ziv, and a value with either "yes" or "no" as to whether they intended the outcome. """

  ## making side-effect = non-intentional explicit
  # system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will recieve a scenario about a person named Ziv, an action they decided to take, and an outcome that happened as a result. You will be asked to judge if Ziv intended the outcome when they took the action. This means that Ziv either took the action specifically to bring about the outcome (it was their goal), or knowing that the outcome was a necessary step to achieve their goal. If the outcome was merely incidental or a side-effect, then they did not intend it, even if they foresaw it. Think step by step. Return a json object with an entry named "results" containing a key with the name of the character, Ziv, and a value with either "yes" or "no" as to whether they intended the outcome. """

  # system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will recieve a scenario about a person named Ziv, an action they decided to take, and an outcome that happened as a result. You will be asked to judge if Ziv intended the outcome when they took the action. This means that Ziv took the action specifically to bring about that outcome, i.e., it was their goal. If the outcome was merely incidental or a side-effect of Ziv's action, then they did not intend it, even if they foresaw it. Think step by step. Return a json object with an entry named "results" containing a key with the name of the character, Ziv, and a value with either "yes" or "no" as to whether they intended the outcome. """


  user_prompt_content = f"""Here is the scenario: {this_scenario} Ziv decides to {this_act} Consider this possible outcome: {this_event}  Did {this_being} intend this outcome to occur in taking their action?"""

  # print(user_prompt_content)       

  return utils.get_response_dict(system_prompt_content, user_prompt_content)




def get_being_links_Ziv_only_know(this_scenario, this_act, this_event, this_being):
    
  system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will receive a scenario about a person named Ziv, an action they decided to take, and an outcome that happened as a result. You will be asked to judge if Ziv expected this outcome to happen. This means that when Ziv took the action, they knew that the outcome would occur. Think step by step. Return a json object with an entry named "results" containing a key with the name of the character, Ziv, and a value with either "yes" or "no" as to whether they expected the outcome to happen."""


  user_prompt_content = f"""Here is the scenario: {this_scenario} Ziv decides to {this_act} Consider this possible outcome: {this_event} Suppose the outcome did happen. Did {this_being} definitely know this outcome would occur when they took the action?"""

  # print(user_prompt_content)       

  return utils.get_response_dict(system_prompt_content, user_prompt_content)





# def get_impacts_Ziv_noscenario(this_scenario, this_act, this_event, these_beings):

#         system_prompt_content = f'You are a helpful assistant who is an expert at understanding human situations. You will be given a description of an event and asked to evaluate how this event on its own (without considering any further consequences) is likely to impact the listed characters. Rate the direct impact on each character using a scale from -10 to +10, where a rating of -10 indicates that the outcome will directly cause the character substantial harm, while a rating of +10 indicates that it will directly cause the character substantial benefit. Please evaluate only the immediate, direct impact of the event on its own, without considering any further consequences or outcomes downstream. If you are not sure that the outcome will immediately and directly affect the character very much, return a rating of 0 or close to 0. Return a json object called "results" with a key:value pair for being: rating.'

#         user_prompt_content = f'Consider the event that {convert_lower(this_event)} Without considering any further consequences of this event, how does this event by itself directly impact each of these characters: {these_beings}?'

#         # print(system_prompt_content, user_prompt_content)
#         return utils.get_response_dict(system_prompt_content, user_prompt_content)




# def score_action_deontology(this_act):

#    system_prompt_content = f"""According to deontological moral theories, the morality of a choice is evaluated based not on the states of affairs those choices bring about, but on the nature of the action itself. These theories hold that some choices cannot be justified by their effects — that no matter how morally good their consequences, some choices are morally forbidden. Instead, what makes a choice right is its conformity with a moral norm. For example, deontological moral theories consider the following moral norms: it is never justified to cause harm or suffering to anyone; that some rules should never be broken, even if breaking them allows for a greater good, and that some principles are universal: they do not depend on circumstances; and that a person’s life is sacred, and killing is always wrong. Consider the following action and rate how well it conforms to deontic moral norms, using a scale from -100 to 100, where -100 indicates that this action is the most extremely deontological wrong action possible, and violates deontic norms in a severe way, and +100 indicates that this action is extremely morally right and conforms to moral norms in a very strong way. A rating of 0 indicates that the action is morally neutral in terms of conformity with moral norms. Please return a json object with key:value pair of "score": rating."""


#    user_prompt_content = f"Please rate this action: {this_act}"     
#    print(system_prompt_content, user_prompt_content)
   
# #    return utils.get_response_dict(system_prompt_content, user_prompt_content)

# def score_action_simple(this_act):
   
#    system_prompt_content = f"""You are an expert judge of the moral virtues of different actions. Moral actions are those which humans consider virtuous, that consider others' wellbeing and happiness, and that are guided by principles of ethics. You will be given a sentence describing an action. You must rate thus action in terms of its moral virtue. Respond with a rating from -100 to 100 for this action, where -100 is the most morally wrong action you can possibly think of, and 100 is the most morally virtuous action you can possibly think of. 0 indicates a morally neutral action. Please return a json object with key:value pair of "score": rating."""

#    user_prompt_content = f"Please rate this action: {this_act}"     
#    print(system_prompt_content, user_prompt_content)

#    return utils.get_response_dict(system_prompt_content, user_prompt_content)


# # pass list of values and score their importance
# def score_values(this_scenario, this_act, values_list):
   
#    system_prompt_content = f"""You are an expert on human values and actions. The user will share a situation and an action they took, plus a list of values and anti-values that the action might have exhibited. Please rate to what extent the action is characterized by each value or anti-value. Use a scale of 0 to 100, where 0 indicates that this value or anti-value does not characterize this action, and 100 indicates that it very much characterizes this action. Return a json object with each value as a key and your rating as a value."""

#    user_prompt_content = f"Here is my situation. {this_scenario} My action is to {this_act} To what extent is this action characterized by these values and anti-values? {values_list}"     



#    return utils.get_response_dict(system_prompt_content, user_prompt_content)


#    system_prompt_content = f"""You are an expert on what humans value and don't value. The user will share an action they chose to take in a situation. Your task is to identify the values and virtues that the user exhibits by taking this action. Return a json object called 'values' listing the values and nothing more."""
          
#     user_prompt_content = f"""Here is my scenario. {this_scenario} My action is to {this_act} List the virtues and values of this action."""

# def get_value_positive(this_scenario, this_act):

#     system_prompt_content = f"""You are an expert on human values. The user will share a situation and an action they decided to take. Identify the most important positive values and virtues that characterize this action. Return a json object called 'values' listing the values and nothing more."""
          
#     user_prompt_content = f"""Here is my scenario. {this_scenario} My action is to {this_act} List the most important values and virtues exhibited by this action."""

   

#     return utils.get_response_dict(system_prompt_content, user_prompt_content)

# def get_value_negative(this_scenario, this_act):

#     system_prompt_content = f"""You are an expert on human vices. The user will share a situation and an action they decided to take. Identify the most important anti-values and vices that characterize this action. Return a json object called 'anti-values' listing the vices and nothing more."""
          
#     user_prompt_content = f"""Here is my scenario. {this_scenario}. My action is to {this_act} List the most important vices exhibited by this action."""
         

#     return utils.get_response_dict(system_prompt_content, user_prompt_content)




# def get_being_links_Ziv_only(this_scenario, this_act, this_event, this_being):
        
#         system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will recieve a scenario about a person named Ziv, an action they took, and an outcome that took place. Answer three questions. 1) Did Ziv directly cause the outcome? If they caused it, it would not occur if they had not acted. 2) Did Ziv expect it would happen as a result of the action?  3) Did Ziv intend for this outcome to occur, either by taking the action or by planning for it? Each question has a yes or no answer. Return a json object with an entry named "results" containing a key with the name of the character, Ziv, and a value with the ordered list of answers to the three questions."""

#         user_prompt_content = f"Here is the scenario: {this_scenario} {this_act} This results in this outcome: {this_event} For the character {this_being}, please answer the three questions relating to the outcome."  

#         print(user_prompt_content)       

#         return utils.get_response_dict(system_prompt_content, user_prompt_content)

# def get_being_links_Ziv(this_scenario, this_act, this_event, this_being):
        
#         system_prompt_content = f"""You are a helpful assistant who is an expert at understanding human situations. You will recieve a scenario about a person named Ziv, an action they took, and an outcome resulting from that action. You will also be given the name of a character. Consider how this character relates to the outcome. Answer three questions. 1) Did they directly cause the outcome? If they caused it, it would not occur if they had not acted. 2) Did they expect it would happen as a result of the action? and 3) Did they intend for this outcome to occur? Each question has a yes or no answer. Return a json object with an entry named "results" containing a key with the name of the character and a value with the ordered list of answers to the three questions."""

#         user_prompt_content = f"Here is the scenario: {this_scenario}. Ziv chose to {this_act}, resulting in this outcome: {this_event}. For the character {this_being}, please answer the three questions relating to the outcome."         

#         return utils.get_response_dict(system_prompt_content, user_prompt_content)
