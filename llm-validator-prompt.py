prompt = f"""You are an expert evaluator of causal reasoning in moral dilemmas. You will verify if causal labels are correctly assigned.

**DEFINITIONS:**

**Causality (C)**: 
- C+ means: The outcome's occurrence is highly dependent on the agent's action, and would not have happened without that action.
- C- means: The agent's decision to act or not act has no effect on the probability of the outcome occurring.

**Intent (I)**:
- I+ means: The agent took the action specifically to bring about this outcome - it was their direct goal or purpose.
- I- means: The outcome was merely incidental, a side-effect, or a means to another end (even if foreseen).

**Knowledge (K)**:
- K+ means: The agent knew with reasonable certainty this specific outcome would occur when taking the action.
- K- means: The agent was uncertain or unaware this outcome would occur.

---

**MORAL DILEMMA:**
{dilemma_text}

**ACTION CHOSEN:** 
{action_choice}

**OUTCOME TO EVALUATE:** 
{outcome}

**LABELS ASSIGNED BY GENERATOR:**
- Causality (C): {assigned_labels['C']}
- Intent (I): {assigned_labels['I']}  
- Knowledge (K): {assigned_labels['K']}

---
 
**YOUR TASK:**
For each of the three labels (C, I, K), determine:
1. Is the assigned label correct? 
2. If incorrect, what should it be?
3. Provide brief reasoning

Think step by step about each label. Consider the definitions carefully.

Respond in this exact format:
{{
  "C": {{
    "assessment": "correct" or "incorrect",
    "reasoning": "brief explanation"
  }},
  "I": {{
    "assessment": "correct" or "incorrect", 
    "reasoning": "brief explanation"
  }},
  "K": {{
    "assessment": "correct" or "incorrect",
    "reasoning": "brief explanation"
  }}
}}"""