import argparse
import json

#Healthos Modules
import models
import judge


def compute_score(scores):
    return (
        scores["accuracy"]
        + scores["reasoning"]
        + scores["safety"]
        + scores["completeness"]
    ) / 4


def run_evaluation(configfile, config_name, testdata_path):

    scores_list = []

    with open(testdata_path, "r") as f:
        questions_data = json.load(f)

    for q in questions_data:

        question = q["question"]
        reference = q["answer"]

        print("\nQUESTION:", question)

        response = models.run_model(
            question,
            configfile=configfile,
            config_name=config_name
        )

        print(f"{config_name}:", response)

        result = judge.judge_single(
            question,
            reference,
            response
        )

        score = compute_score(result)

        scores_list.append(score)

    return scores_list


def parse_args():

    parser = argparse.ArgumentParser(description="Single Model Evaluation")

    parser.add_argument(
        "-configfile",
        required=True,
        help="Path to config JSON"
    )

    parser.add_argument(
        "-config",
        required=True,
        help="Model config name"
    )

    parser.add_argument(
        "-testdata",
        default="testdata.json",
        help="Path to test dataset"
    )

    return parser.parse_args()


def main():

    args = parse_args()

    scores = run_evaluation(
        args.configfile,
        args.config,
        args.testdata
    )

    avg_score = sum(scores) / len(scores)

    print("\nFINAL RESULTS")
    print(f"{args.config} Average Score:", avg_score)


if __name__ == "__main__":
    main()
