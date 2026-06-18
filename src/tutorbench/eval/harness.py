def qwk(human, pred) -> float:
    """Quadratic Weighted Kappa (QWK) metric."""
    from sklearn.metrics import cohen_kappa_score
    return cohen_kappa_score(human, pred, weights="quadratic")

def mae(human, pred) -> float:
    """Mean Absolute Error (MAE) metric."""
    return sum(abs(h - p) for h, p in zip(human, pred)) / len(human)

def run_eval(gold_path, *, grader) -> dict:
    """Run evaluation: load gold data, grade with the provided grader, compute metrics."""
    import json
    with open(gold_path) as f:
        gold = json.load(f)
    human = [item["human_score"] for item in gold]
    pred = [grader(item["question"], item["answer"]) for item in gold]
    return {
        "qwk": qwk(human, pred),
        "mae": mae(human, pred),
    }
def main():
    import argparse
    parser = argparse.ArgumentParser(description="Evaluate a grading model against gold data.")
    parser.add_argument("gold_path", help="Path to the gold data JSON file.")
    args = parser.parse_args()
    
    # Example grader function; replace with actual model grading logic.
    def example_grader(question, answer):
        return len(answer) % 5  # Dummy prediction based on answer length.
    
    results = run_eval(args.gold_path, grader=example_grader)
    print("Evaluation Results:")
    print(f"Quadratic Weighted Kappa: {results['qwk']:.4f}")
    print(f"Mean Absolute Error: {results['mae']:.4f}")