import pandas as pd
import nltk
from sklearn.feature_extraction.text import CountVectorizer
from nltk.stem import WordNetLemmatizer#,PorterStemmer
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords#, wordnet
import es_core_news_sm
from collections import  Counter
#nltk.download('wordnet')

log = []

def get_top_ngram(corpus, n=None, count=20):
    log.append('init n top')
    vec = CountVectorizer(ngram_range=(n, n)).fit(corpus)
    log.append('after CountVectorizer')
    bag_of_words = vec.transform(corpus)
    sum_words = bag_of_words.sum(axis=0) 
    words_freq = [(word, sum_words[0, idx]) for word, idx in vec.vocabulary_.items()]
    words_freq =sorted(words_freq, key = lambda x: x[1], reverse=True)
    return words_freq[:count]


def get_frecuency_words(count, df_texto):
    def build_list(df,col="observacion"):
        corpus=[]
        lem=WordNetLemmatizer()
        stop=set(stopwords.words('spanish'))
        new= df[col].dropna().str.split()
        new=new.values.tolist()
        corpus=[lem.lemmatize(word.lower()) for i in new for word in i if(word) not in stop]
        
        return corpus    
    stop=set(stopwords.words('spanish'))
    corpus=build_list(df_texto)
    counter=Counter(corpus)
    most=counter.most_common(n=count)
    x=[]
    y=[]
    for word,i in most[:count]:
        if (word not in stop) :
            x.append(word)
            y.append(i)
    return dict(x=x, y=y)

def get_n_grama(n,count, df_texto):
    log.append('init n grama')
    top_n_grams=get_top_ngram(df_texto['observacion'].dropna(),n=n, count=count)
    log.append('after call get top ngram')
    x,y=map(list,zip(*top_n_grams))
    log.append('after map')
    y = [int(n) for n in y]
    return dict(x=x, y=y)