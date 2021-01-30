import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import CountVectorizer
from sklearn.feature_extraction.text import TfidfTransformer
from sklearn.naive_bayes import MultinomialNB
from sklearn.linear_model import LogisticRegression
from sklearn.feature_selection import chi2

def build_ml_model():
    #data = pd.read_csv('internal\machine_learning\datasets\my_collected_dataset.csv')
    data = pd.read_csv('internal\machine_learning\datasets\\full_set.csv')
    #data.columns = ['Phrase', 'User', 'Leaning']
    data.columns = ['Leaning', 'Phrase']
    data['leaning_id'] = data['Leaning'].factorize()[0]
    leaning_id_df = data[['Leaning', 'leaning_id']].drop_duplicates().sort_values('leaning_id')
    leaning_to_id = dict(leaning_id_df.values)
    from sklearn.svm import LinearSVC

    tfidf = TfidfVectorizer(sublinear_tf=True, min_df=5, norm='l2', encoding='utf-8', ngram_range=(1, 2), stop_words='english')

    features = tfidf.fit_transform(data.Phrase.astype('U').values)
    labels = data.leaning_id
    features.shape

    x_train, x_test, y_train, y_test = train_test_split(data['Phrase'], data['Leaning'], random_state = 0, test_size=0.33)
    word_count_vect = CountVectorizer()
    X_train_counts = word_count_vect.fit_transform(x_train.astype('U').values)

    tfidf_transformer = TfidfTransformer()
    X_train_tfidf = tfidf_transformer.fit_transform(X_train_counts)
    tclf = LogisticRegression(random_state=0).fit(X_train_tfidf, y_train)
    
    prediction = tclf.predict(word_count_vect.transform(x_test))
    #print(np.mean(prediction == y_test))
    
    return tclf, word_count_vect

def predict_from_model(model, word_count_vect, text_data):
    prediction = model.predict(word_count_vect.transform([text_data]))
    prob = model.predict_proba(word_count_vect.transform([text_data]))
    return prediction

def test():
    model, word_count_vect = build_ml_model()
    prediction = predict_from_model(model, word_count_vect, "Trump is very bad")
 
# Describe the leaning of a political score
def describe_political_leaning(political_score):
    statement = ""
    if political_score < -0.3:
        statement = "These tweets align more closely with right-leaning than left-leaning tweets from the training dataset"
    elif political_score > 0.3:
        statement = "These tweets align more closely with left-leaning than right-leaning tweets from the training dataset"
    else:
        statement = "These tweets have no strong political leaning"
    return statement
    
#test()