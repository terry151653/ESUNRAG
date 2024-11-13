import json
import argparse

def calculate_precision(predictions_path, ground_truth_path):
    """
    Calculate the precision of model predictions by comparing with ground truth data.
    
    Args:
        predictions_path (str): Path to the JSON file containing model predictions.
                              Expected format: {"answers": [{"qid": str, "retrieve": list}, ...]}
        ground_truth_path (str): Path to the JSON file containing ground truth data.
                                Expected format: {"ground_truths": [{"qid": str, "retrieve": list}, ...]}
    
    Returns:
        None. Prints the precision score and any mismatched predictions.
    """
    # Load ground truth data
    with open(ground_truth_path, 'r', encoding='utf-8') as f:
        ground_truths = json.load(f)['ground_truths']

    # Load prediction data 
    with open(predictions_path, 'r', encoding='utf-8') as f:
        predictions = json.load(f)['answers']

    # Calculate precision by comparing predictions with ground truths
    correct = 0
    total = len(predictions)

    for pred, truth in zip(predictions, ground_truths):
        if pred['retrieve'] == truth['retrieve']:
            correct += 1
        else:
            print(f"QID: {pred['qid']}")
            print(f"Prediction: {pred['retrieve']}, Ground Truth: {truth['retrieve']}")

    precision = correct / total
    print(f"Precision: {precision:.4f}")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Calculate precision of model predictions against ground truth data.')
    parser.add_argument('--predictions',
                        type=str, 
                        required=True, 
                        default="./dataset/preliminary/example_pre_retrieval.json", 
                        help='Path to predictions JSON file')
    parser.add_argument('--ground_truth', 
                        type=str, 
                        required=True, 
                        default="./dataset/preliminary/ground_truths_example.json", 
                        help='Path to ground truth JSON file')
    
    args = parser.parse_args()
    
    calculate_precision(args.predictions, args.ground_truth)
