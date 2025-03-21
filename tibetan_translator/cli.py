import argparse
from tqdm.notebook import tqdm
from tibetan_translator.workflow import optimizer_workflow
from tibetan_translator.utils import convert_state_to_jsonl, get_json_data


def run(data, batch_size=4, run_name="run1", preprocess=False):
    """Run the translation workflow on the given data.

    Args:
        data (list): The list of dictionaries containing the data.
        batch_size (int): The batch size to process.
        run_name (str): The name of the run to save the output files.
        preprocess (bool): Whether to preprocess the data before running the workflow.
    """
    examples = []
    if preprocess:
        for i in tqdm(data, desc="Creating input dictionaries"):
            examples.append({
                "source": i["root"],
                "sanskrit": i["sanskrit"],
                "commentary1": i.get("commentary_1", ""),
                "commentary2": i.get("commentary_2", ""),
                "commentary3": i.get("commentary_3", ""),
                "feedback_history": [],
                "format_feedback_history": [],
                "itteration": 0,
                "format_iteration": 0,
                "formated": False,
                "glossary": [],
                "language": "English"
            })
    else:
        examples = data

    batches = [examples[i:i + batch_size] for i in range(0, len(examples), batch_size)]
    results = []

    for batch in tqdm(batches, desc="Processing batches"):
        try:
            batch_results = optimizer_workflow.batch(batch)
            for result in batch_results:
                convert_state_to_jsonl(result, f"{run_name}.jsonl")
            results.extend(batch_results)
        except Exception as e:
            print(f"Error processing batch: {e}")
            for failed in batch:
                convert_state_to_jsonl(failed, f"{run_name}_fail.jsonl")
    
    return results


def run_translation_pipeline(input_file: str, output_file: str, batch_size=4, preprocess=False):
    """Run the translation workflow on the given input file and save results."""
    data = get_json_data(input_file)
    results = run(data, batch_size=batch_size, run_name=output_file, preprocess=preprocess)
    print(f"Translation process completed. Results saved in {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Tibetan Translator CLI")
    parser.add_argument("--input", type=str, required=True, help="Path to input JSON file")
    parser.add_argument("--output", type=str, required=True, help="Path to output JSONL file")
    parser.add_argument("--batch_size", type=int, default=4, help="Batch size for processing")
    parser.add_argument("--preprocess", action='store_true', help="Whether to preprocess data before running")
    
    args = parser.parse_args()
    run_translation_pipeline(args.input, args.output, batch_size=args.batch_size, preprocess=args.preprocess)


if __name__ == "__main__":
    main()
