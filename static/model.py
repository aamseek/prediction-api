import pandas as pd
import numpy as np
from matplotlib import pyplot as plt
from sklearn import linear_model
from sklearn.preprocessing import PolynomialFeatures
from sklearn.model_selection import train_test_split
from sklearn.metrics import accuracy_score
from sklearn.metrics import recall_score
from sklearn.metrics import f1_score
from sklearn.metrics import precision_score
from sklearn.metrics import roc_curve
from sklearn.metrics import roc_auc_score
from sklearn.metrics import precision_recall_curve
from sklearn.metrics import auc
import seaborn as sns
import math
import itertools
import warnings

# Ignoring the warnings
warnings.filterwarnings('ignore')

# Set the format to two decimal places
pd.options.display.float_format = '{:20,.2f}'.format

# Lets start training on data by reading data.csv file
data = pd.read_csv('data.csv')

# Make lead ID as index so that its easy to pick data on the basis of lead ID
data.set_index('lead_id', inplace=True)

# For now, we don't need CIBIL score hence dropping the col. altogether. Maybe it will be used in Future...
data.drop(['dmi_cibil_score'], axis = 1, inplace=True)

# Removed leads where sal. is more then 50000 and 500000 per month
data = data[(data['salary'] > 5000) & (data['salary'] < 500000)]
print("Sample Count",len(data.index))

# Total loan amount
data['loan_total_total'] = data.filter(like='_loan_total').sum(axis=1)
# data['loan_max_total'] = data.filter(like='_loan_max').sum(axis=1)
# data['loan_total_max'] = data.filter(like='_loan_total').max(axis=1)
data['loan_max_max'] = data.filter(like='_loan_max').max(axis=1)

# EMI
data['emi_total_total'] = data.filter(like='_emi_total').sum(axis=1)
# data['emi_total_max'] = data.filter(like='_emi_total').max(axis=1)
# data['emi_max_total'] = data.filter(like='_emi_max').sum(axis=1)
data['emi_max_max'] = data.filter(like='_emi_max').max(axis=1)

# To remove anomalyise
data = data[(data['loan_total_total'] < 100000000) & (data['loan_total_total'] >= 1000)]

cols = data.columns[(data.columns.str.contains('_loan_')|data.columns.str.contains('_card_')|data.columns.str.contains('overdraft_'))]
data[cols] = data[cols].mask(data[cols] < 1000)

cols = data.columns[data.columns.str.contains('_emi_')]
data[cols] = data[cols].mask(data[cols] < 100)

print("sample count",len(data.index))
pd.set_option('display.max_columns', None)
backup_data = data[data.columns.drop(list(data.filter(regex='count')))]

data = backup_data.copy()
data.replace(0,np.nan, inplace=True)
data = data.loc[:, ~data.columns.str.endswith('_loan_total')]
data = data.loc[:, ~data.columns.str.endswith('_emi_total')]
data = data.loc[:, data.isnull().mean() < .98]
data.head(50)

data = backup_data.copy()
y = np.where(data.salary >= 25000,1,0)
X = data.drop('salary', 1)
# X = data[['loan_total_total','credit_card_max']]
X['cat2'] = np.where(data.salary >= 20000,1,0)

X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.25, random_state=0)
X_train.fillna(0, inplace=True)
X_test.fillna(0, inplace=True)
y2_train = X_train['cat2']
X_train.drop('cat2', axis=1, inplace=True)
y2_test = X_test['cat2']
X_test.drop('cat2', axis=1, inplace=True)

from sklearn.linear_model import LogisticRegression
model = LogisticRegression(penalty = 'l2', C = 0.1,random_state = 0)
model.fit(X_train, y_train)
print(model.score(X_train, y_train))
predicted= model.predict_proba(X_test)[:,1]
y_true = y2_test
y_score = [1 if a_ > 0.59 else 0 for a_ in predicted]

# Compute fpr, tpr, thresholds and roc auc
fpr, tpr, thresholds = roc_curve(y_score,y_true)
# roc_auc = auc(y_true, y_score)

# Plot ROC curve
plt.plot(fpr, tpr, label='ROC curve (area = %0.3f)')
plt.plot([0, 1], [0, 1], 'k--')  # random predictions curve
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.0])
plt.xlabel('False Positive Rate or (1 - Specifity)')
plt.ylabel('True Positive Rate or (Sensitivity)')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")

print("Accuracy:- ",accuracy_score(y_test, y_score))
print("Precision Score:- ",precision_score(y_test, y_score))
print("Recall Score:- ",recall_score(y_test, y_score))
print("F1 Score:- ",f1_score(y_test, y_score))
print("AUC:- ",roc_auc_score(y_test, y_score))
print(y_test.tolist())
print(y_score)
print(predicted.tolist())

precision, recall, thresholds = precision_recall_curve(y_test, y_score)
plt.plot(precision, recall)

from sklearn.linear_model import LogisticRegression
model = LogisticRegression(random_state = 0)
model.fit(X_train, y_train)
print(model.score(X_train, y_train))
predicted= model.predict_proba(X_test)[:,1]
y_true = y2_test
y_score = [1 if a_ > 0.53 else 0 for a_ in predicted]

# Compute fpr, tpr, thresholds and roc auc
fpr, tpr, thresholds = roc_curve(y_score,y_true)
# roc_auc = auc(y_true, y_score)

# Plot ROC curve
plt.plot(fpr, tpr, label='ROC curve (area = %0.3f)')
plt.plot([0, 1], [0, 1], 'k--')  # random predictions curve
plt.xlim([0.0, 1.0])
plt.ylim([0.0, 1.0])
plt.xlabel('False Positive Rate or (1 - Specifity)')
plt.ylabel('True Positive Rate or (Sensitivity)')
plt.title('Receiver Operating Characteristic')
plt.legend(loc="lower right")

print("accuracy:-",accuracy_score(y2_test, y_score))
print("precision score:-",precision_score(y2_test, y_score))
print("recall score:-",recall_score(y2_test, y_score))
print("f1 score:-",f1_score(y2_test, y_score))
print("AUC :-",roc_auc_score(y2_test, y_score))
print(y2_test.tolist())
print(y_score)
print(predicted.tolist())

pd.options.display.float_format = '{:20,.12f}'.format
coefficients = pd.concat([pd.DataFrame(X_train.columns),pd.DataFrame(np.transpose(model.coef_))], axis = 1)
print(coefficients)
interc = model.intercept_
print(interc[0]*10000)
print(model.coef_)

import pickle
pickle.dump(model, open("model.pkl", "wb"))