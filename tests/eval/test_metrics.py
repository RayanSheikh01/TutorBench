import pytest


def test_qwk_identical():
    from tutorbench.eval.harness import qwk
    assert qwk([0, 1, 2, 3, 4], [0, 1, 2, 3, 4]) == 1.0
    
def test_qwk_known():
    from tutorbench.eval.harness import qwk
    # 4 ratings over categories 1-4 with a single 3->2 disagreement.
    # Quadratic weights (i-j)^2/(N-1)^2 give QWK = 1 - (1/9)/(10/9) = 0.9.
    human = [1, 2, 3, 4]
    pred = [1, 2, 2, 4]
    expected_qwk = 0.9
    assert abs(qwk(human, pred) - expected_qwk) < 1e-6
    
def test_mae():
    from tutorbench.eval.harness import mae
    human = [0, 1, 2, 3, 4]
    pred = [0, 1, 1, 3, 5]
    expected_mae = (0 + 0 + 1 + 0 + 1) / 5
    assert abs(mae(human, pred) - expected_mae) < 1e-6
    
def test_run_eval_with_fake_grader(tmp_path):
    from tutorbench.eval.harness import run_eval
    
    # Create fake gold data
    gold_data = [
        {"question": "Q1", "answer": "A1", "human_score": 2},
        {"question": "Q2", "answer": "A2", "human_score": 3},
        {"question": "Q3", "answer": "A3", "human_score": 1},
    ]
    gold_path = tmp_path / "gold.json"
    with open(gold_path, 'w') as f:
        import json
        json.dump(gold_data, f)
    
    # Define a fake grader that returns fixed scores
    def fake_grader(question, answer):
        return {"Q1": 2, "Q2": 2, "Q3": 0}[question]
    
    results = run_eval(gold_path, grader=fake_grader)
    
    # Check that results contain expected keys and values
    assert "qwk" in results
    assert "mae" in results
    assert isinstance(results["qwk"], float)
    assert isinstance(results["mae"], float)
