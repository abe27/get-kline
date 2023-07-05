import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.linear_model import LogisticRegression

# Load historical data or use your own dataset
df = pd.read_csv('IXIC.csv')

# Prepare features and target variable
X = df[['feature1', 'feature2', 'feature3']]  # Add relevant features
y = df['target']  # Replace 'target' with your target variable column

# Split the data into training and testing sets
X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)

# Train a logistic regression model
model = LogisticRegression()
model.fit(X_train, y_train)

# Predict the market direction
prediction = model.predict(X_test)

# Convert predictions to 'bullish' or 'bearish' labels
prediction_labels = ['bullish' if pred == 1 else 'bearish' for pred in prediction]

# Evaluate the model
accuracy = model.score(X_test, y_test)
print(f"Accuracy: {accuracy:.2f}")

# Print the predictions
print("Market Predictions:")
for pred_label in prediction_labels:
    print(pred_label)