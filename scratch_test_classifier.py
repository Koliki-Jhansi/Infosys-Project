import json
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

train_data = json.load(open('data/training_dataset.json', encoding='utf-8'))
eval_data = json.load(open('data/evaluation_dataset.json', encoding='utf-8'))

X_train = [x['text'] for x in train_data]
y_train = [x['category'] for x in train_data]

X_eval = [f"{x['title']} {x['description']}" for x in eval_data]
y_eval = [x['expected_category'] for x in eval_data]

pipe_nb = Pipeline([('tfidf', TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)), ('clf', MultinomialNB(alpha=0.05))])
pipe_nb.fit(X_train, y_train)
acc_nb = pipe_nb.score(X_eval, y_eval)

pipe_lr = Pipeline([('tfidf', TfidfVectorizer(ngram_range=(1,2), sublinear_tf=True)), ('clf', LogisticRegression(C=5.0, max_iter=500))])
pipe_lr.fit(X_train, y_train)
acc_lr = pipe_lr.score(X_eval, y_eval)

print(f'NB Accuracy: {acc_nb*100:.2f}%')
print(f'LR Accuracy: {acc_lr*100:.2f}%')
