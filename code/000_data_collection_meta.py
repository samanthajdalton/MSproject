
import gzip
from bs4 import BeautifulSoup
import urllib
import re

import urllib2
import json
import csv
import time
from __future__ import division


###Set proxy info
proxy = urllib2.ProxyHandler({'http': 'http://sjdalton:Babycat1@proxy.indra.es:8080/'})
opener = urllib2.build_opener(proxy)
urllib2.install_opener(opener)


use_proxy = 'YES'
path = "/media/jupiter/hadoopuser/amazon/data/"
pull_ids = 'NO'
get_meta_info = 'YES'
scrape_meta_info ='YES'
if use_proxy == 'NO':
    proxy=''

import requests
opener = urllib2.build_opener(proxy)
opener.addheaders = [('User-agent', 'Mozilla/5.0')]

#change to category name of items scraping
#if change from drill, need to change text filter in line 198
category_name="drill"


###These should be URLS of product search pages selected by the user (contain 20 products/page)

#exclude brush,case, reconditioned, refurbished & title must have drill

urlList=["http://www.amazon.com/s/ref=sr_nr_p_36_2?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253530011&keywords=drill&ie=UTF8&qid=1432901118&rnid=1243644011",
      "http://www.amazon.com/s/ref=sr_pg_2?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253530011&page=2&keywords=drill&ie=UTF8&qid=1432901605",
      "http://www.amazon.com/s/ref=sr_pg_3?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253530011&page=3&keywords=drill&ie=UTF8&qid=1432901711",
      "http://www.amazon.com/s/ref=sr_pg_4?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253530011&page=4&keywords=drill&ie=UTF8&qid=1432901836",
      "http://www.amazon.com/s/ref=sr_pg_5?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253530011&page=5&keywords=drill&ie=UTF8&qid=1432901865"
      "http://www.amazon.com/s/ref=sr_pg_7?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253530011&page=7&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432902412",
      "http://www.amazon.com/s/ref=sr_nr_p_36_1?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253529011&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432902528&rnid=1243644011",
      "http://www.amazon.com/s/ref=sr_pg_2?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253529011&page=2&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432902543",
      "http://www.amazon.com/s/ref=sr_pg_3?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253529011&page=3&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432902595",
      "http://www.amazon.com/s/ref=sr_pg_4?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253529011&page=4&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432902708",
      "http://www.amazon.com/s/ref=sr_nr_p_36_3?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253531011&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432902528&rnid=1243644011",
      "http://www.amazon.com/s/ref=sr_pg_2?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253531011&page=2&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432902869",
      "http://www.amazon.com/s/ref=sr_pg_3?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253531011&page=3&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432902933",
      "http://www.amazon.com/s/ref=sr_pg_4?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253531011&page=4&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432903010",
      "http://www.amazon.com/s/ref=sr_pg_5?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253531011&page=5&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432903143",
      "http://www.amazon.com/s/ref=sr_pg_6?fst=as%3Aoff&rh=n%3A228013%2Cn%3A328182011%2Cn%3A551236%2Cn%3A552794%2Cn%3A9022404011%2Ck%3Adrill%2Cp_n_feature_four_browse-bin%3A9060577011%2Cp_36%3A1253531011&page=6&sort=relevancerank&keywords=drill&ie=UTF8&qid=1432903114"]


def get_soup(url):
    opener = urllib2.build_opener(proxy)
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    r1=opener.open(url)
    #r1=requests.get(url)
    soup = BeautifulSoup(r1.read(),'html.parser')
    ids=[ re.findall("[0-9A-Z]{10}",item)[0] for  item in re.findall("data-asin=\"[0-9A-Z]{10}\"",str(soup))]
    return ids



file_name= path+category_name+"_ids.txt"

if pull_ids == 'YES':
    listOfIds=[get_soup(item) for item in urlList]
    listOfIds2=list(set(str(listOfIds).replace("[","").replace("]","").replace(",","").replace("'","").split()))
    with open(file_name,"w") as f:
        f.write(str(listOfIds2).replace("[","").replace("]",""))
else:
    print('Not rerunning to pull ids')



####get product info


#Function to Get product meta data
def get_meta(asin):
    meta={}
    amazonUrl = 'http://www.amzn.com/'
    url= amazonUrl + asin
    opener = urllib2.build_opener(proxy)
    opener.addheaders = [('User-agent', 'Mozilla/5.0')]
    r = opener.open(url)
    s = BeautifulSoup(r.read())
    print(str(s)[0:20])
    print(asin)
    meta["asin"] = asin
    meta["productTitle"] = s.find_all(id="productTitle")[0].get_text()
    meta["category"]=str(re.findall("\S+\s", s.find_all(id="wayfinding-breadcrumbs_feature_div")[0].get_text().encode('ascii','ignore'))).replace("'",'').replace(",",'').replace("[",'').replace("]",'').split("\\n")    
    meta["scrapeDate"] = int(time.time())
    try:
        meta["ladderSalesRank"]=re.sub("#",'',s.find_all("span", class_="zg_hrsr_rank")[0].get_text()).replace(',','')
        meta["categoryLadder"]=[item.get_text() for item in s.find_all("span", class_="zg_hrsr_ladder")[0].find_all("a")]
    except:
        meta["ladderSalesRank"]="Rescrape"
        meta["categoryLadder"]="Rescrape"
    try:
        meta["mainCategorySalesRank"]=re.findall("[^A-Za-z\s]+",s.find_all(id="SalesRank")[0].find_all("td",class_="value")[0].get_text().replace('\n',''))[0].replace('#','').replace(',','')
        meta["mainCategory"]=re.findall("[A-Za-z\s]+",s.find_all(id="SalesRank")[0].find_all("td",class_="value")[0].get_text().replace('\n',''))[0].replace(' in','')
    except:
        meta["mainCategorySalesRank"]="Rescrape"
        meta["mainCategory"]="Rescrape"


    try:
        meta["price"] = str(s.find_all(id="priceblock_ourprice")[0].get_text())
    except:
        meta["price"] = "unavailable"
    try:
        meta["shipping"] = str(s.find_all(id="ourprice_shippingmessage")[0].get_text().replace('\n',''))
    except:
        meta["shipping"] = "unavailable"
    try:
        meta["savings"] = re.findall("\$[0-9]*.[0-9]*", str(s.find_all(id="regularprice_savings")[0].get_text()))[0]
    except:
         meta["savings"] = 0
    try:        
        meta["description"] = s.find_all(id="feature-bullets")[0].get_text().encode('ascii','ignore').replace('\n','').replace('See more product details','')
    except:
        meta["description"] = unknown
    try:
        meta["dateFirstAvailable"] = [item.find(class_="value").get_text() for item in s.find_all("tr")                                   if str(item).find("date-first-available") > -1][0]
    except:
        meta["dateFirstAvailable"] = 'unavailable'
    try:
        meta["productsPurchasedAfter"]=[item.replace("reviews/","") for  item in set(re.findall("reviews/[0-9A-Z]{10}",               str(s.find_all(id="view_to_purchase-sims-feature")[0].find_all(class_="a-link-normal"))))]
    except:
        meta["productsAlsoViewed"]='Unknown'
    try:
        meta["otherSellers"] = s.find_all(id="mbc")[0].get_text().encode('ascii','ignore').replace('\n','')
    except:
        meta["otherSellers"] = 'unavailable'
    try:
        meta["numOfReviews"]=int(re.findall("[^A-Za-z\s]+",s.find_all(id="acrCustomerReviewText")[0].get_text())[0].replace(",",''))
    except:
        meta["numOfReviews"]= 0
    return meta


######Use product Ids collected from search pages to scrape prices

if scrape_meta_info=='YES':
    if pull_ids == 'NO':
        list_of_ids=open(path+category_name+"_ids.txt","r")
        asin_list=list(set(list_of_ids.read().replace("'",'').replace(",","").split()))
        list_of_ids.close()
    else:
        print('Using new ids pulled and stored in memory')

    url_error=[]

    file_name=path+"meta_" + category_name + time.strftime("%Y%m%d") + ".txt"
    with open(file_name,"w") as f:
        meta_info=[]
        for idx,item in enumerate(asin_list):
            print(str(idx) +' ' + item)
            try:
                info=get_meta(item)
                meta_info.append(info)
                f.write(json.dumps(info) + ',')
                time.sleep(randint(4,7))
                if (idx % 30) == 0 & idx!=0:
                    time.sleep(100)
            except:
                url_error.append(item)

######GET META INFO (PRICE AND SALES RANK INFO)

if scrape_meta_info=='NO':
    if get_meta_info=='YES':
        text=open(path+"meta_" + category_name+"s" + time.strftime("%Y%m%d") + ".txt", "r").read()
        import ast
        meta_info=ast.literal_eval(text)

if scrape_meta_info=='YES' or get_meta_info=='YES':        
    asins_to_keep=[]
    meta_info1=[]
    counter=0
    for idx,item in enumerate(meta_info):
        try:
            if int(item["numOfReviews"]) >= 20:
            #if item["numOfReviews"] == "Unknown":
                if item["productTitle"].lower().find(category_name) > -1:
                    counter += 1
                    asins_to_keep.append(item["asin"])
                    meta_info1.append(item)
        except:
            None


    meta_json = json.dumps(obj = meta_info1,indent = 4)
    fd = open(path + "meta_" + category_name + "_final_" + time.strftime("%Y%m%d") + ".json", "w")
    fd.write(meta_json)
    fd.close()



outfile=open(path + "meta_" + category_name + "_final.txt","w")
ids=[row["asin"].encode('ascii','ignore') for row in meta_info1]
print(ids)
outfile.write("\n".join(ids))
