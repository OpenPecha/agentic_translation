def run(data,batch_size=4,optimizer_workflow,run_name="run1",preprocess=False):
    """Run the translation workflow on the given data.

    Args:
        data (list): The list of dictionaries containing the data.
        batch_size (int): The batch size to process.
        optimizer_workflow (StateGraph): The compiled optimizer workflow.
        run_name (str): The name of the run to save the output files.
        preprocess (bool): Whether to preprocess the data before running the workflow.
    """

    examples = []
    if preprocess:
    

        for i in tqdm(data, desc="Creating input dictionaries"):
            examples.append({
                "source": i["root"],
                "sanskrit": i["sanskrit"],
                "commentary1": i["commentary_1"],
                "commentary2": i["commentary_2"],
                "commentary3": i["commentary_3"],
                "feedback_history": [],
                "format_feedback_history": [],
                "itteration": 0,
                "formated": False,
                "glossary": [],
                'language': "English"
            })

    # Create batches of size 3
    batch_size = batch_size
    batches = [examples[i:i + batch_size] for i in range(0, len(examples), batch_size)]

    # Now process each batch
    results = []
    for batch in tqdm(batches, desc="Processing batches"):
        try:
            results = optimizer_workflow.batch(batch)
            [convert_state_to_jsonl(i,f"{run_name}.jsonl") for i in results]
        except Exception as e:
            print(e)
            [convert_state_to_jsonl(i,f"{run_name}_fail.jsonl") for i in batch]