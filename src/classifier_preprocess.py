import string
import os
import csv
import cPickle
import numpy as np
import pandas as pd
from nltk.tokenize import RegexpTokenizer
from nltk import pos_tag
from nltk.stem import PorterStemmer
from gensim.models.keyedvectors import KeyedVectors
from keras.models import Sequential
from keras.layers import LSTM, Activation, Dense
from keras.preprocessing.sequence import pad_sequences

class NLTKPreprocessor(object):
    def __init__(self):
        self.punct      = set(string.punctuation)
        self.stemmer=PorterStemmer()
    def inverse_transform(self, X):
        return [" ".join(doc) for doc in X]

    def transform(self, X):
        return list(self.tokenize(X))

    def tokenize(self, sentence):
        tokenizer=RegexpTokenizer(r'\w+')
        # Break the sentence into part of speech tagged tokens
        tokenized_words=[]
        for token, tag in pos_tag(tokenizer.tokenize(sentence)):
            token = token.lower()
            token = token.strip()

            # If punctuation, ignore token and continue
            if all(char in self.punct for char in token):
                continue

            # Stem the token and yield
            try:
                stemmed_token=self.stemmer.stem(token).encode('utf-8')
            except:
                print "Unicode error. File encoding was changed when you opened it in Excel. ",
                print "This is most probably an error due to csv file from Google docs being opened in Word. ",
                print "Download the file from Google Docs and DO NOT open it in Excel. Run the program immediately. ",
                print "If you want to edit using Excel and then follow instructions at: "
                print "http://stackoverflow.com/questions/6002256/is-it-possible-to-force-excel-recognize-utf-8-csv-files-automatically"
                continue
            yield stemmed_token

class ClassifierPreProcess(object):
    def __init__(self):
        self.train_data=[]
        self.test_data=[]
        self.train_vectors=[]
        self.test_vectors=[]
        self.lstm_train_vectors=[]
        self.lstm_test_vectors=[]
        self.lstm_train_data=[]
        self.lstm_test_data=[]
        self.answer_ids={}
        self.ids_answer={}
        self.all_topics=[]
        self.last_id=0
        self.w2v_model=None
        self.topic_model=None
        self.topic_set=set()
        self.preprocessor=NLTKPreprocessor()


    def read_topics(self):
        with open('data/topics.csv') as f:
            reader=csv.reader(f)
            for row in reader:
                self.all_topics.append(row[0].lower())

    def normalize_topics(self, topics):
        ret_topics=[]
        for topic in topics:
            topic=topic.strip()
            topic=topic.lower()
            ret_topics.append(topic)
            self.topic_set.add(topic)
        return ret_topics

    def read_data(self):
        corpus=pd.read_csv('data/classifier_data.csv')
        corpus=corpus.fillna('')
        total=0
        for i in range(0,len(corpus)):
            topics=corpus.iloc[i]['topics'].split(",")

            questions=corpus.iloc[i]['question'].split('\r\n')
            questions=filter(None, questions)
            total+=len(questions)
            paraphrases=questions[1:]
            current_question=questions[0]

            answer=corpus.iloc[i]['text']
            answer_id=corpus.iloc[i]['ID']

            self.answer_ids[answer]=answer_id
            self.ids_answer[answer_id]=answer

            #Tokenize the question
            processed_question=self.preprocessor.transform(current_question)
            topics=filter(None, topics)
            #normalize the topics
            topics=self.normalize_topics(topics)

            #add question to dataset
            self.train_data.append([current_question,processed_question,topics,answer_id])
            #look for paraphrases and add them to dataset
            for i in range(0,len(paraphrases)):
                processed_paraphrase=self.preprocessor.transform(paraphrases[i])
                if i==len(paraphrases)-1:
                    self.test_data.append([paraphrases[i],processed_paraphrase,topics,answer_id])
                else:
                    self.train_data.append([paraphrases[i],processed_paraphrase,topics,answer_id])

    def get_w2v(self, question):
        current_vector=np.zeros(300,dtype='float32')
        lstm_vector=[]
        for word in question:
            try:
                word_vector=self.w2v_model[word]
            except:
                word_vector=np.zeros(300,dtype='float32')
            lstm_vector.append(word_vector)
            current_vector+=word_vector
        return current_vector, lstm_vector

    def generate_training_vectors(self):
        #for each data point, get w2v vector for the question and store in train_vectors.
        #instance=<question, topic, answer, paraphrases>
        for instance in self.train_data:
            w2v_vector, lstm_vector=self.get_w2v(instance[1])
            self.train_vectors.append([instance[0],w2v_vector,instance[2],instance[3]])
            self.lstm_train_vectors.append(lstm_vector)
        padded_vectors=pad_sequences(self.lstm_train_vectors,maxlen=25, dtype='float32',padding='post',truncating='post',value=0.)
        self.lstm_train_vectors=padded_vectors

        try:
            for instance in self.test_data:
                w2v_vector, lstm_vector=self.get_w2v(instance[1])
                self.test_vectors.append([instance[0],w2v_vector,instance[2],instance[3]])
                self.lstm_test_vectors.append(lstm_vector)
            padded_vectors=pad_sequences(self.lstm_test_vectors,maxlen=25, dtype='float32',padding='post',truncating='post',value=0.)
            self.lstm_test_vectors=padded_vectors
        except:
            pass

    def generate_sparse_topic_vectors(self):
        #Generate the sparse topic train_vectors
        for i in range(len(self.train_vectors)):
            question=self.train_vectors[i][0]
            vector=self.train_vectors[i][1]
            current_topics=self.train_vectors[i][2]
            topic_vector=[0]*len(self.all_topics)
            for j in range(len(self.all_topics)):
                if self.all_topics[j] in current_topics:
                    topic_vector[j]=1
            self.train_vectors[i][2]=topic_vector
            self.lstm_train_data.append([question,self.lstm_train_vectors[i],topic_vector])

        try:
            #Generate the sparse topic test_vectors
            for i in range(len(self.test_vectors)):
                question=self.test_vectors[i][0]
                vector=self.test_vectors[i][1]
                current_topics=self.test_vectors[i][2]
                topic_vector=[0]*len(self.all_topics)
                for j in range(len(self.all_topics)):
                    if self.all_topics[j] in current_topics:
                        topic_vector[j]=1
                self.test_vectors[i][2]=topic_vector
                self.lstm_test_data.append([question,self.lstm_test_vectors[i],topic_vector])
        except:
            pass


    def write_data(self):
        if not os.path.exists('train_data'):
            os.mkdir('train_data')
        if not os.path.exists('test_data'):
            os.mkdir('test_data')

        #dump lstm_train_data
        with open('train_data/lstm_train_data.pkl','wb') as pickle_file:
            cPickle.dump(self.lstm_train_data, pickle_file)
        #dump train_vectors for logistic regression
        with open('train_data/lr_train_data.pkl','wb') as pickle_file:
            cPickle.dump(self.train_vectors,pickle_file)
        try:
            #dump lstm_test_data
            with open('test_data/lstm_test_data.pkl','wb') as pickle_file:
                cPickle.dump(self.lstm_test_data, pickle_file)
            #dump test_vectors for logistic regression
            with open('test_data/lr_test_data.pkl','wb') as pickle_file:
                cPickle.dump(self.test_vectors,pickle_file)
        except:
            pass
        #dump ids_answers
        with open('train_data/ids_answer.pkl','wb') as pickle_file:
            cPickle.dump(self.ids_answer,pickle_file)

