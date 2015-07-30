
# coding: utf-8


import gzip
from bs4 import BeautifulSoup
import urllib
import re

import urllib2
import json
import csv
import time
from __future__ import division


proxy = urllib2.ProxyHandler({'http': 'http://sjdalton:Babycat1@proxy.indra.es:8080/'})
opener = urllib2.build_opener(proxy)
urllib2.install_opener(opener)

#if you don't want to use proxy, change this to NO
use_proxy='YES'
path="/media/jupiter/hadoopuser/amazon/data/"
pull_ids='NO'
get_meta_info='YES'
scrape_meta_info='YES'
if use_proxy=='NO':
    opener = urllib2.build_opener()
    urllib2.install_opener(opener)

import requests

opener.addheaders = [('User-agent', 'Mozilla/5.0')]


#change to category name of items scraping
#if change from drill, need to change text filter in line 198
category_name="drill"
fd = open(path + "meta_" + category_name + "_final" + ".json", "r")
text=fd.read()
meta_info  = json.loads(text)


###Get Reviews####
AMAZON_URL = 'http://www.amzn.com/product-reviews/'
ref1='/ref=cm_cr_pr_viewopt_srt?ie=UTF8&pageNumber='
ref2='&sortBy=recent&reviewerType=all_reviews&filterByStar=all_stars'
#url = AMAZON_URL + asin +ref1 + str(pageNo) +ref2

#Grabs soup for the nth page of reviews order by date
def get_soup(asin,pageNo):
    opener = urllib2.build_opener()
    opener.addheaders = [('User-agent', 'Chrome/42.0.2311.90')]
    soup_info={}
    url = AMAZON_URL + asin +ref1 + str(pageNo) +ref2
    r = opener.open(url)    
    s = BeautifulSoup(r.read())   
    soup_info["asin"] = asin
    soup_info["url"] = url
    soup_info["soup"]= s
    soup_info["pageNo"] = pageNo
    return soup_info

#gets information from the soup object
def get_review_info(s,list_name):
    totReviews=len(s["soup"].find_all(class_="a-section review"))
    listReviews= s["soup"].find_all(class_="a-section review")
    if s["pageNo"]==1:
       
        pages["asin"]=s["asin"]
        pages["noReviewPages"]=str(s["soup"].find_all(class_="page-button")[len(s["soup"].find_all(class_="page-button"))-1].get_text())
        asin_pages.append(pages)
    for R in listReviews:
        rev={}
        rev["asin"]=s["asin"]
        rev["reviewPageNo"]=s["pageNo"]
        rev["reviewText"]=R.find_all(class_="a-row review-data")[0].get_text()
        rev["reviewDate"]=R.find_all(class_=re.compile("review-date"))[0].get_text().replace("on","")
        rev["reviewId"]=R.get("id")
        try:
            rev["reviewAuthor"]=R.find_all(class_=re.compile("author"))[0].get_text()
        except:
            rev["reviewAuthor"]='Unknown'
        rev["reviewTitle"]=R.find_all(class_=re.compile("review-title"))[0].get_text()
        rev["reviewStars"]=R.find_all(class_=re.compile("a-icon-alt"))[0].get_text()
        try:
            rev["reviewVerified"]=R.find_all(class_="a-size-mini a-color-state a-text-bold")[0].get_text()
        except:
            rev["reviewVerified"]="Not verified"    
        try:
            rev["helpfulCount"]=R.find_all(class_="a-row helpful-votes-count")[0].get_text()
        except:
            rev["helpfulCount"]=0
        list_name.append(rev)


###Read in product ids and number of review pages ####
##get asin id and number of review pages for each product
import math
import pandas as pd
reviews=[]
asin_pages=[]

for item in meta_info:
    pages={}
    pages["noReviewPages"]=math.ceil(int(item["numOfReviews"])/10)
    pages["asin"]=item["asin"]
    asin_pages.append(pages)
    
   
asinPages=pd.DataFrame(asin_pages)


##order ids by fewest number of review pages
asinPages=asinPages.sort(("noReviewPages","asin"))
asinList=[items for items in asinPages.ix[:,0]]


error_list=[]
from random import randint

for idx,items in enumerate(missing):
    print(items)   
    with open(path +"reviews_drill_"+ str(items) +".json", "w") as fd:
        pages={}
        #Block the line below out if process stalls in the middle of one product's downloads 
        #and change the range to the page stalled so you don't have to rerun entire product again
        reviews2=[]    
        soup_info=get_soup(items,1)
        info=get_review_info(soup_info, reviews2) 
        pageNo=int(pages["noReviewPages"])
        print(pageNo)
        for i in range(2,pageNo+1):
            soup_info=get_soup(items,i)
            info=get_review_info(soup_info, reviews2)
            time.sleep(randint(10,15))        
            if i % 7 ==0 and idx !=0:  
                print(i)
                time.sleep(5)
        fd.write(json.dumps(reviews2)) 
        print(str(i)+' pages scraped')
        print(len(reviews2))       
        time.sleep(20)
        if idx % 30 ==0 and idx !=0:
                print(idx)
                time.sleep(100)

###For troubleshooting, please see .ipynb version of this file

#########################DUMP ALL REVIEWS INTO JSON FILE ########

import os
import re
finished=[re.findall("B[0-9]{2}[0-9A-Z]{7}",filename)[0] for filename      in os.listdir(path) if filename.find('reviews_drill_B')>-1]

#read in all individual product reviews json files
reviews=[]
for id in finished:
    fd = open(path+"reviews_drill_" + id + ".json", "r")
    text = fd.read()
    pmeta = json.loads(text)
    reviews = reviews + pmeta
    fd.close()

#Write all reviews out to file    
reviews2 = json.dumps(obj = reviews,indent = 4)
fd = open(path+category_name+"_reviews_" + time.strftime("%Y%m%d") + ".json", "w")
fd.write(reviews2)
fd.close()

len(reviews)    

