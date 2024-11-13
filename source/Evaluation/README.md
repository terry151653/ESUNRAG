# Evaluation Workflow

### Calculating Precision

Use the `calc_precision.py` script to calculate the precision of your model's predictions.

```bash
python ./source/Evaluation/calc_precision.py --predictions [path_to_predictions] --ground_truth [path_to_ground_truth]
```

for example:

```bash
python ./source/Evaluation/calc_precision.py --predictions ./dataset/preliminary/my_pred_retrieve.json --ground_truth ./dataset/preliminary/ground_truths_example.json
```
