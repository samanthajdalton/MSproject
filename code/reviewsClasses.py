# -*- coding: utf-8 -*-
"""
Created on Thu Jun 11 19:35:09 2015

@author: Samantha Dalton
"""
import numpy as np
import codecs
import nltk

from nltk.tokenize import wordpunct_tokenize
from nltk import PorterStemmer
from nltk.corpus import stopwords



class Review():

        def __init__(self, review_dict):
            self.asin = review_dict['asin'].encode('ascii','ignore')
            self.reviewId = review_dict['reviewId'].encode('ascii','ignore')
            self.reviewAuthor = review_dict['reviewAuthor'].encode('ascii','ignore')
            self.reviewDate = review_dict['reviewDate'].encode('ascii','ignore')
            self.reviewText = review_dict['reviewText'].encode('ascii','ignore').lower()
            self.tokens = np.array(wordpunct_tokenize(self.reviewText))
            self.reviewPageNo = review_dict['reviewPageNo'] 
            self.reviewStars = int(review_dict['reviewStars'].encode('ascii','ignore')) 
            self.helpfulCount = review_dict['helpfulCount'].encode('ascii','ignore') 
            self.verified = review_dict['reviewVerified'].encode('ascii','ignore')
            self.reviewTitle = review_dict['reviewTitle'].encode('ascii','ignore')
            


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
            
class ReviewCollection():
        def __init__(self, doc_data, stopword_file):
    
            self.docs = [Review(doc) for doc in doc_data] 
            self.stopwords = [word for word in stopwords.words('english') if word not in ['no', 'not','don','again','very'] ]     
            self.N = len(self.docs)
            #stopword removal, token cleaning and stemming to docs
            self.clean_docs(1)
            #creates a set of all doc tokens
            self.docs_tokens = self.create_docs_tokens()
            
        def clean_docs(self, length):
            """ 
            Applies stopword removal, token cleaning and stemming to docs
            """
            for doc in self.docs:
                doc.token_clean(length)
                doc.stopword_remove(self.stopwords)
                doc.stem()
                
        def count(self, dictionary):
            """ 
            word count frequency of dictionary in document collection
            """
            
            return ({(doc.pid) : \
                     doc.tf(dictionary) for doc in self.docs})
        
        def idf(self, dictionary):
            """ 
            returns array of inverted document frequency for given dictionary 
            over collection of docs
            """
            
            is_word_docs = np.array([doc.word_exists(dictionary) for doc in self.docs])
            
            asum = sum([is_word for is_word in is_word_docs])
            asum_sum = sum(asum)
            
            if asum_sum != 0:
                idf_list = np.log(self.N / asum )
            else:
                idf_list = np.zeros(len(dictionary))
                
            return idf_list            