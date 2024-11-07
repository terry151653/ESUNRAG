import json
import os

# Load ground truth data
with open(os.path.join('..', 'dataset', 'preliminary', 'ground_truths_example.json'), 'r', encoding='utf-8') as f:
    ground_truths = json.load(f)['ground_truths']

# Load prediction data 
with open(os.path.join('..', 'dataset', 'preliminary', 'my_pred_retrieve.json'), 'r', encoding='utf-8') as f:
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
