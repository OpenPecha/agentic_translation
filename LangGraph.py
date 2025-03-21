

# # Post translation 




glossary= pd.read_csv('Glossary_.csv')
inputs= pd.read_csv('inputs.csv')



def generate_standardization_examples(glossary, translation_file, max_samples_per_term=10):
    """
    Generate standardization examples for Tibetan terms with multiple translation candidates, 
    limiting each term to at most 10 examples.
    
    Parameters:
    -----------
    glossary : pandas.DataFrame
        DataFrame containing Tibetan terms and their translations.
        Must have columns 'tibetan_term' and 'translation_freq'.
    
    translation_file : pandas.DataFrame
        DataFrame containing source texts and translations.
        Must have columns 'source', 'translation', and 'sanskrit'.
    
    max_samples_per_term : int, optional
        Maximum number of translation examples to include per Tibetan term (default is 10).
    
    Returns:
    --------
    list
        List of standardization example strings.
    """
    examples = []
    
    # Ensure no NaN values in 'source' column to prevent masking error
    translation_file['source'] = translation_file['source'].fillna("")

    for i in range(len(glossary)):
        # Check if there are multiple translation candidates
        translation_candidates = glossary.iloc[i]['translation_freq'].split(';')
        
        if len(translation_candidates) > 1:
            # Get the Tibetan term
            tibetan_term = glossary.iloc[i]['tibetan_term']
            
            # Find samples containing this term, handling NaN values
            term_mask = translation_file['source'].str.contains(tibetan_term, na=False)
            samples = translation_file[term_mask][['source', 'translation', 'sanskrit']]

            # Limit to a maximum of 10 examples
            samples = samples.head(max_samples_per_term)
            
            # Build the example text
            example = f"Usage examples:\n\n"
            
            # Add each sample (limited to max_samples_per_term)
            for _, sample in samples.iterrows():
                example += f"Sanskrit: {sample['sanskrit']}\n"
                example += f"Source: {sample['source']}\n"
                example += f"Translation: {sample['translation']}\n\n"
            
            # Add the Tibetan term and translation candidates
            example += f"Tibetan Term: {tibetan_term} Translation: {glossary.iloc[i]['translation_freq'].replace(';', ',')}\n\n"
            
            # Add the standardization protocol
            example += """Translation Standardization Protocol:

1. Context Compatibility Analysis: Evaluate each candidate translation by substituting it across all attested examples to ensure semantic congruence in every context.

2. Canonical Alignment: When parallel Sanskrit attestations exist, prioritize translations that maintain terminological correspondence with the Sanskrit source tradition while remaining comprehensible in English.

3. Hierarchical Selection Criteria:
   a. Cross-contextual applicability (primary determinant)
   b. Terminological ecosystem coherence (relationship to established glossary terms)
   c. Register appropriateness for target audience

4. Validation Through Bidirectional Testing: Verify that the standardized term maps consistently back to the Tibetan term without ambiguity or semantic drift.

Output:
Tibetan Term: [Tibetan term]
Selected standard translation: [Selected translation]
Rationale: [Brief explanation of why this translation was selected based on the rules]"""
            
            examples.append(example)

    return examples

# Call function with a max of 10 examples per term
prompts = generate_standardization_examples(glossary, inputs, max_samples_per_term=20)


# In[6]:


import ast
import pandas as pd
standardised_words_df = pd.read_csv('standard_translation.csv')
def standard_tibetan_term_extractor(glossary):
    """
    Extract Tibetan terms and their translations from the glossary.
    
    Parameters:
    -----------
    glossary : pandas.DataFrame.series
        Contains list of dict with ['tibetan_term']
    
    Returns:
    --------
    str
        A string containing the Tibetan terms, separated by commas.
    """
    terms = []
    for item in ast.literal_eval(glossary):
        if item['tibetan_term'] in list(standardised_words_df['tibetan_term']):
            term = item['tibetan_term']
            terms.append(term)
    
    # Join all collected terms with commas
    return ", ".join(terms) if terms else ""


# In[9]:


inputs['tibetan_term']= inputs['glossary'].map(standard_tibetan_term_extractor)


# In[10]:


inputs[inputs['tibetan_term']!='']


# In[15]:


class Word_standardization(BaseModel):
    standard_translation: str = Field(
        description="The standard translation of the word",
    )
    tibetan_term: str = Field(
        description="The tibetan term to be standardized",
    )
    rationale: str = Field(
        description="The rationale for the standardization",
    )
    target_audience: str = Field(
        description="ranked target audience for the standardization, separated by commas",
    )


# In[16]:


wordstandardizer=llm.with_structured_output(Word_standardization)


# In[17]:


from tqdm.notebook import tqdm

standardised_words = []
# for example in tqdm(a, desc="Standardizing words"):
#     result = wordstandardizer.invoke(example)
#     standardised_words.append(dict(result))

#batched standardization
dict_ = a
batch_size = 30
batches = [dict_[i:i + batch_size] for i in range(0, len(dict_), batch_size)]

# Now process each batch
results = []
for batch in tqdm(batches, desc="Processing batches"):
    try:
        result = wordstandardizer.batch(batch)
        standardised_words.extend(result)
    except Exception as e:
        print(e)
        result = wordstandardizer.batch(batch)
        standardised_words.extend(result)


# In[237]:


dict(standardised_words[0])['standard_translation']
dict(standardised_words[0])['tibetan_term']
dict(standardised_words[0])['rationale']
dict(standardised_words[0])['target_audience']
new_standardised_words = []
for i in standardised_words:
    new_standardised_words.append(dict(i))
    


# In[238]:


import pandas as pd 
standardised_words_df = pd.DataFrame(new_standardised_words)


# In[239]:


standardised_words_df.to_csv("standard_translation.csv")


# In[253]:


inputs['tibetan_term']


# In[18]:


dict_= []

def dict_to_text(d, indent=0):
    text = ""
    spacing = " " * indent

    for i in d:
    
        for key, value in i.items():
            if isinstance(value, dict):
                text += f"{spacing}{key}:-{dict_to_text(value, indent+4)}"
            else:
                text += f"{spacing}{key}:-{value}\n"
        
    return text



for i in inputs[inputs['tibetan_term']!=""].iterrows():
    glossary=[]
    for j in i[1]['tibetan_term'].split(', '):
        if j in standardised_words_df.index:
            glossary.append({'tibetan_term': j, 'standard_translation': standardised_words_df.loc[j]['standard_translation']})
        else:
            print(f"Warning: '{j}' not found in standardised_words_df. Skipping.")




    prompt=f"""
Standardize the following translation by ONLY replacing non-standard terminology with the approved equivalents from the glossary. Ensure the resulting text remains natural and accurate.

SOURCE TEXT:
{i[1]['source']}

RAW TRANSLATION:
{i[1]['translation']}

STANDARDIZED GLOSSARY:
{dict_to_text(glossary)}

COMMENTARY (for context only):
{i[1]['combined_commentary']}

INSTRUCTIONS:
1. Identify terms in the raw translation that have standardized equivalents in the glossary
2. Replace ONLY those specific terms with their standardized versions
3. Make minimal adjustments if necessary to maintain grammatical correctness
4. Do not change any other aspects of the translation
5. Ensure the final text reads naturally and preserves the original meaning and format

STANDARDIZED TRANSLATION:
[Provide standardized translation here]

WORD-BY-WORD TRANSLATION:
Format: [Tibetan word/phrase] → [English translation]

Example:
བྱང་ཆུབ་སེམས་དཔའ་ → bodhisattva
སྒོམ་པ་ → meditation
ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་ → perfection of wisdom
རྣམ་པར་ཤེས་པ་ → consciousness

[Continue with word-by-word mapping for the entire text]
    """


    dict_.append(prompt) 


# In[19]:


len(dict_)


# In[20]:


dict_[0]

class Post_Translation(BaseModel):
    standardised_translation: str = Field(
        description="The standardised translation of the source text",
    )


# In[21]:


post_translator=llm.with_structured_output(Post_Translation)


# In[22]:


arr=[]
# standardised_words = []
# # for example in tqdm(a, desc="Standardizing words"):
# #     result = wordstandardizer.invoke(example)
# #     standardised_words.append(dict(result))

# #batched standardization
# dict_ = a
# batch_size = 20
# batches = [dict_[i:i + batch_size] for i in range(0, len(dict_), batch_size)]

# # Now process each batch
# results = []
# for batch in tqdm(batches, desc="Processing batches"):
#     try:
#         result = wordstandardizer.batch(batch)
#         standardised_words.extend(result)
#     except Exception as e:
#         print(e)
#         result = wordstandardizer.batch(batch)
#         standardised_words.extend(result)


dict_ = dict_
batch_size = 30
batches = [dict_[i:i + batch_size] for i in range(0, len(dict_), batch_size)]

# Now process each batch
for batch in tqdm(batches, desc="Processing batches"):
    try:
        results = post_translator.batch(batch)
        arr.extend(result.standardised_translation for result in results)
    except Exception as e:
        print(e)
        result = post_translator.batch(batch)
        arr.extend(result.standardised_translation for result in results)


# In[263]:





# In[118]:


sherp_nyingpo['word by word translation']= ["" for i in range(len(sherp_nyingpo))]


# In[23]:


inputs.loc[inputs['tibetan_term']!="",['translation']]= [i for i in arr]


# In[27]:


inputs.columns


# In[24]:


class Word_by_word_translation(BaseModel):
    word_by_word_translation: str = Field(
        description="The word by word translation of the source text",
    )

word_by_word_translator=llm.with_structured_output(Word_by_word_translation)   
word_by_word = []
dict_=[]
for i in tqdm(inputs.iterrows(),total=inputs.shape[0]):

    prompt= f"""
        Given source text and translation, create a word-by-word translation based on the standardized translation. Ensure the word-by-word translation accurately reflects the meaning of the standardized translation.

        Source Text:
        {i[1]['source']}

        Standardized Translation:

        {i[1]['translation']}

        WORD-BY-WORD TRANSLATION:
        Format: [Tibetan word/phrase] → [English translation]

        Example:
        བྱང་ཆུབ་སེམས་དཔའ་ → bodhisattva
        སྒོམ་པ་ → meditation
        ཤེས་རབ་ཀྱི་ཕ་རོལ་ཏུ་ཕྱིན་པ་ → perfection of wisdom
        རྣམ་པར་ཤེས་པ་ → consciousness

        [Continue with word-by-word mapping for the entire text]

        """
    dict_.append(prompt)
    
    
  

dict_ = dict_
batch_size = 20
batches = [dict_[i:i + batch_size] for i in range(0, len(dict_), batch_size)]
arr=[]

# Now process each batch
for batch in tqdm(batches, desc="Processing batches"):
    try:
        results = word_by_word_translator.batch(batch)
        arr.extend(result.word_by_word_translation for result in results)
    except Exception as e:
        print(e)
        result = word_by_word_translator.batch(batch)
        arr.extend(result.word_by_word_translation for result in results)



# In[26]:


inputs['word by word translation']


# In[34]:


inputs_new[['source','plaintext_translation','combined_commentary','translation','word by word translation']].to_json('inputs_final_cleaned.json', orient='records', force_ascii=False, indent=4)


# In[196]:


