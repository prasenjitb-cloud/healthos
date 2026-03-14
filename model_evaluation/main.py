import questions
import models
import judge

def compute_score(scores):

    return (
        scores["accuracy"]
        + scores["reasoning"]
        + scores["safety"]
        + scores["completeness"]
    ) / 4


def run_evaluation():

    biomed_scores = []
    tiny_scores = []

    for q in questions.questions:

        question = q["question"]
        reference = q["answer"]

        print("\nQUESTION:", question)

        biomed, tiny = models.run_models(question)

        print("BioMedLM:", biomed)
        print("TinyLlama:", tiny)

        result = judge.judge(question, reference, biomed, tiny)

        a_score = compute_score(result["model_a"])
        b_score = compute_score(result["model_b"])

        biomed_scores.append(a_score)
        tiny_scores.append(b_score)

    return biomed_scores, tiny_scores

def main():
    biomed_scores, tiny_scores = run_evaluation()
    
    biomed_avg = sum(biomed_scores) / len(biomed_scores)
    tiny_avg = sum(tiny_scores) / len(tiny_scores)
    
    print("\nFINAL RESULTS")
    
    print("BioMedLM Average:", biomed_avg)
    print("TinyLlama Average:", tiny_avg)
    
    if biomed_avg > tiny_avg:
        print("BioMedLM performs better in medical context")
    else:
        print("TinyLlama performs better")

if __name__ == "__main__":
    main()
