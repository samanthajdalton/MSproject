# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 19:35:09 2015

@author: Samantha Dalton
"""
import numpy as np
import codecs
import nltk
import json
import pandas as pd
import lda

from nltk.tokenize import wordpunct_tokenize
from nltk import PorterStemmer
from nltk.corpus import stopwords
from nltk.stem.wordnet import WordNetLemmatizer

import sklearn.feature_extraction.text as sk
import matplotlib


wnl = WordNetLemmatizer()


class Review():

    def __init__(self, review_dict):
        self.asin = review_dict['asin'].encode('ascii','ignore')
        self.reviewId = review_dict['reviewId'].encode('ascii','ignore')
        self.reviewAuthor = review_dict['reviewAuthor'].encode('ascii','ignore')
        self.reviewDate = review_dict['reviewDate'].encode('ascii','ignore')
        self.reviewText = review_dict['reviewText_new'].encode('ascii','ignore').lower()
        self.reviewText_orig=review_dict['reviewText']
        self.text = None    
        self.tokens = np.array(wordpunct_tokenize(self.reviewText))
        #self.cleanTokens = np.array(self.clean_doc())       
        self.reviewPageNo = review_dict['reviewPageNo'] 
        self.reviewStars = int(review_dict['reviewStars'].encode('ascii','ignore')) 
        self.helpfulCount = review_dict['helpfulCount'].encode('ascii','ignore') 
        self.verified = review_dict['reviewVerified'].encode('ascii','ignore')
        self.reviewTitle = review_dict['reviewTitle'].encode('ascii','ignore')
        
        
    #Strip out non alpha token            

    #Remove stopwords
    def stopword_remove(self, stop):
        self.tokens = np.array([t for t in self.tokens if t not in stop])
        self.tokens= np.array([t for t in self.tokens if len(t) > 2])
        self.tokens= np.array([t for t in self.tokens if t not in ['drill','tool','amazon']])
        
    #Stem tokens with Porter Stemmer
    def stem(self, choice):
        if choice=='PS':           
            self.tokens = np.array([PorterStemmer().stem(t) for t in self.tokens])
        if choice=='L':
            wnl = WordNetLemmatizer()
            self.tokens = np.array([wnl.lemmatize(t) for t in self.tokens])
    #sentiment dictionary score     
    def sentiment(self, harvard_wrdlist_dict, afinn_score_dict):
        if len(self.tokens) != 0:
            
            self.sentiment_afinn = sum([afinn_score_dict[token] for token in self.tokens if token in afinn_score_dict.keys()]) \
            / len(self.tokens) 
            self.sentiment_pos = sum([1 for token in self.tokens if token in harvard_wrdlist_dict["positive"]]) \
            / len(self.tokens)
            self.sentiment_neg = sum([1 for token in self.tokens if token in harvard_wrdlist_dict["negative"]]) \
            / len(self.tokens)

    def mod_sentiment(self, harvard_wrdlist_dict, afinn_score_dict):
        self.sentiment_afinn = 0
        self.sentiment_pos = 0 
        self.sentiment_neg = 0
        
        if len(self.tokens) != 0:
            prev_token = ""
            for token in self.tokens:
                if token in afinn_score_dict.keys():
                    if prev_token == "not":
                        self.sentiment_pos -= 1
                        self.sentiment_neg -= 1
                        self.sentiment_afinn -= afinn_score_dict[token] 
                    else:
                        self.sentiment_pos += 1
                        self.sentiment_neg += 1
                        self.sentiment_afinn += afinn_score_dict[token]
                prev_token = token
        
        self.sentiment_afinn = self.sentiment_afinn / len(self.tokens)
        self.sentiment_pos = self.sentiment_pos / len(self.tokens)
        self.sentiment_neg = self.sentiment_neg / len(self.tokens)
        

##########Collection of Reviews Class            
class ReviewCollection():
    
    def __init__(self, doc_data, choice, keepList=None):
    
        self.docs = [Review(doc) for doc in doc_data] 
        if keepList is None:
            self.stopword = stopwords.words('english')   
        else:
            self.stopword= [word for word in stopwords.words('english') if word not in keepList] 
        self.N = len(self.docs)
        #stopword removal, token cleaning and stemming to docs
        self.clean_docs(choice)
        #creates a set of all doc tokens
        self.collection_tokens = self.create_docs_tokens()
        self.remove_0()
       
    #removes stopwords        
    def clean_docs(self,choice):
        for doc in self.docs:
            doc.stopword_remove(self.stopword)
            doc.stem(choice)
            doc.text = " ".join(doc.tokens)
            
    def remove_0(self):
        new_docs = [doc for doc in self.docs if len(doc.tokens) != 0]
        self.docs = new_docs
        
        N = self.N
        self.N = len(self.docs)
        
        print("docs removed:", str(N - self.N))
                
                    
    #Get set of all document token         
    def create_docs_tokens(self):

        doc_tokens = set()
        
        for doc in self.docs:
            doc_tokens.update(doc.tokens)
            
        return doc_tokens
    
    #Function to get panda data frame for document term matrix
    def get_doc_term_mat(self):

        doc_text = []
        doc_ids = []
        for doc in self.docs:
            doc_text.append(doc.text)
            doc_ids.append(doc.reviewId)
            
        vectorizer = sk.CountVectorizer(lowercase=False)
        word_counts = vectorizer.fit_transform(doc_text)
        
        dtm = pd.DataFrame(word_counts.toarray(), columns = vectorizer.get_feature_names())
        dtm.rename(index = pd.Series(doc_ids), inplace= True)
        
        return dtm
   
    
    #Fits an LDA to each review for topic analysis
    def lda(self, doc_term_mat = None, num_topics = 10, n_iter = 1500):
        #because only need to caculate once
        if doc_term_mat is None:
            doc_term_mat = self.get_doc_term_mat()
        #taking column names in vocab    
        vocab = doc_term_mat.columns.values
        #Converting doc term matrix to numpy array
        doc_term_mat = doc_term_mat.as_matrix(columns=vocab)
        doc_term_mat = doc_term_mat.astype("int64")
        
        #train lda
        model = lda.LDA(n_topics= num_topics, n_iter= n_iter, random_state=1)
        model.fit(doc_term_mat)  # model.fit_transform(X) is also available
        
        return model, vocab

    #Function to get sentiment of   (would only do this at the product level if desired)           
    def collection_sentiment(self, harvard_wrdlist_dict, afinn_score_dict):
        """
        calculates sentiment for the entire collection
        """
        for doc in self.docs:
            doc.sentiment(harvard_wrdlist_dict, afinn_score_dict)    
    
    def mod_collection_sentiment(self, harvard_wrdlist_dict, afinn_score_dict):
        """
        calculates sentiment for the entire collection
        """
        for doc in self.docs:
            doc.mod_sentiment(harvard_wrdlist_dict, afinn_score_dict)    
    

      
        
###################################################

class ProductInfo():

        def __init__(self, product_dict):
            self.asin =  product_dict['asin']
            self.category = product_dict['category']
            self.description = product_dict['description'].encode('ascii','ignore').lower()
            self.numOfReviews = int(product_dict['numOfReviews'])
            self.productTitle = product_dict['productTitle'].encode('ascii','ignore').lower()
            self.tokens = np.array(wordpunct_tokenize(self.description))
            self.price = product_dict['price'].encode('ascii','ignore')
            self.shipping = product_dict['shipping'].encode('ascii','ignore') 
            self.dateFirstAvailable = product_dict['dateFirstAvailable'] 
            self.savings = product_dict['savings'].encode('ascii','ignore')
            self.scrapeDate = product_dict['scrapeDate']       
            self.otherSellers = product_dict['otherSellers']
