import argparse
import json
import os
from datetime import datetime

# HealthOS Modules
import models
import judge


def compute_score(scores):
    return (
        scores["accuracy"]
        + scores["reasoning"]
        + scores["safety"]
        + scores["completeness"]
    ) / 4


def load_config(configfile):
    with open(configfile, "r") as f:
        return json.load(f)


def save_results(results, config_name, output_dir="results"):
    """Save per-test results and final summary to a timestamped JSON file."""

    os.makedirs(output_dir, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"{config_name}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    valid_scores = [r["score"] for r in results if r["score"] is not None]
    avg_score = sum(valid_scores) / len(valid_scores) if valid_scores else None

    output = {
        "model": config_name,
        "timestamp": timestamp,
        "total_tests": len(results),
        "valid_tests": len(valid_scores),
        "average_score": avg_score,
        "tests": results
    }

    with open(filepath, "w") as f:
        json.dump(output, f, indent=2)

    print(f"\nResults saved to: {filepath}")
    return filepath


def run_evaluation(configfile, config_name, testdata_path, output_dir="results"):

    scores_list = []
    all_results = []

    # Load config
    config = load_config(configfile)

    # Initialize judge components ONCE
    llm = judge.load_llm(config)
    prompt = judge.build_prompt(pairwise=False)

    model, model_config = models.load_model(configfile, config_name)

    # Load dataset
    with open(testdata_path, "r") as f:
        questions_data = json.load(f)

    for i, q in enumerate(questions_data):

        question = q["question"]
        reference = q["answer"]

        print(f"\n[Test {i + 1}/{len(questions_data)}] QUESTION: {question}")

        # Generate response
        response = models.run_model(
            question=question,
            configfile=configfile,
            config_name=config_name,
            model=model,
            model_config=model_config
        )

        print(f"{config_name}:", response)

        # Judge evaluation
        result = judge.judge_single(
            llm,
            prompt,
            question,
            reference,
            response
        )

        # Build per-test record
        test_record = {
            "test_index": i + 1,
            "question": question,
            "reference": reference,
            "response": response,
            "scores": None,
            "score": None,
            "error": None
        }

        # Handle possible parsing errors
        if "error" in result:
            print("Judge Error:", result["error"])
            test_record["error"] = result["error"]
        else:
            score = compute_score(result)
            test_record["scores"] = result
            test_record["score"] = round(score, 4)
            scores_list.append(score)
            print(f"Score: {score:.2f}")

        all_results.append(test_record)

    # Save all results to file
    save_results(all_results, config_name, output_dir)

    return scores_list


def parse_args():

    parser = argparse.ArgumentParser(description="Single Model Evaluation")

    parser.add_argument(
        "--configfile",
        required=True,
        help="Path to config JSON"
    )

    parser.add_argument(
        "--config",
        required=True,
        help="Model config name"
    )

    parser.add_argument(
        "--testdata",
        default="testdata.json",
        help="Path to test dataset"
    )

    parser.add_argument(
        "--output_dir",
        default="results",
        help="Directory to save output results (default: results/)"
    )

    return parser.parse_args()


def main():

    args = parse_args()

    scores = run_evaluation(
        args.configfile,
        args.config,
        args.testdata,
        args.output_dir
    )

    if len(scores) == 0:
        print("\nNo valid scores generated.")
        return

    avg_score = sum(scores) / len(scores)

    print("\nFINAL RESULTS")
    print(f"{args.config} Average Score:", avg_score)


if __name__ == "__main__":
    main()
