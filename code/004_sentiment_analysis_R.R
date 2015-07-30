

if (!require("tm")) install.packages("tm")
library(tm)

if (!require("topicmodels")) install.packages("topicmodels")
library(topicmodels)

if (!require("ggplot2")) install.packages("ggplot2")
library(ggplot2)

if (!require("plyr")) install.packages("plyr")
library(plyr)


if (!require("nnet")) install.packages("nnet")
library(nnet)

# loading the raw data

#from mongoDB table of reviews, just output mongo to csv rather than use mongo driver
reviews_text<-read.csv('/media/jupiter/hadoopuser/amazon/data/drill_reviews_table_text.csv',
                  header = TRUE,  
                  stringsAsFactors = FALSE, colClasses="character")


stopwords <- stopwords("SMART") # stopwords from package tm

# loading the sentiment dictionary with weights

sentimentWords <- read.table(file = "/media/jupiter/hadoopuser/amazon/data/sentimentWords.txt",
                             header = FALSE, sep = "\t",
                             quote = "", col.names = c("word", "weight"))


# splitting the dictionary into positive and negative depending on the weights

positiveWords <- subset(sentimentWords, weight > 0)
rownames(positiveWords) <- NULL
negativeWords <- subset(sentimentWords, weight < 0)
rownames(negativeWords) <- NULL


################################################################################
######                     EXTRACTING THE CONTENT                          #####
################################################################################


# 1. BREAK STATEMENTS INTO TOKENS

createTokens <- function(text){
  
  corpus = Corpus(VectorSource(text)) # create the Corpus format
  corpus = tm_map(corpus, scan_tokenizer) # tokenize keeping the multi-words expressions
  
  
  # 2. REMOVE UNNECESSARY SIGNS LIKE PUNCTUATIONS AND NUMBERS
  
  # 2.1 Remove numbers
  
  corpus = tm_map(corpus, removeNumbers)
  
  # 2.2 Remove e-mail addresses as there are many in the WHO source
  # I have to do it before removing the punctuations as I won't be able to localize them
  
  for (i in seq(corpus)){   
    corpus[[i]] <- gsub("(\\b\\S+\\@\\S+\\..{1,3}(\\s)?\\b)", "", corpus[[i]])
  }
  
  # 2.3 Remove punctuations
  
  corpus = tm_map(corpus, removePunctuation, preserve_intra_word_dashes = TRUE)
  
  # 2.4 Remove other unnecessary special characters in case there are any
  # (except "-" which connects multi-words expressions)
  
  for (i in seq(corpus)){
    corpus[[i]] <- gsub('[^a-zA-Z0-9-]','', corpus[[i]])
  }
  
  # 2.5 CONVERT ALL WORDS TO LOWER CASE
  
  corpus = tm_map(corpus, tolower)
  
  
  # 3. REMOVE STOPWORDS
  
  corpus = tm_map(corpus, removeWords, stopwords)
  
  # remove empty elements
  for (i in seq(corpus)){
    corpus[[i]] <- corpus[[i]][corpus[[i]] != ""]
  }
  return(corpus)
}

# Creating the corpuses
reviewCorpus <- createTokens(reviews_text$reviewText)

#####################calculating sentiment score per document in dictionary ####
calculateScore <- function(corpus, dictionary){
  
  finalScore <- c()
  for(i in seq(corpus)){
    
    matches <- match(corpus[[i]],dictionary$word)
    matches <- subset(matches,matches > 0)
    
    totalScore <- 0
    
    for (j in matches){
      
      score <- dictionary$weight[j]
      totalScore <- totalScore + score
      
    }
    finalScore[i] <- totalScore
  }
  return(finalScore)
}



### USE OF THE ABOVE FUNCTION TO CALCULATE THE SENTIMENT PER DOCUMENT


scorePos <- calculateScore(reviewCorpus,positiveWords)
sum(scorePos)
scoreNeg <- calculateScore(reviewCorpus,negativeWords)
sum(scoreNeg)
names(reviews_text)
###Attach pos and negative scores to dataframe
review_sent<-cbind(reviews_text[,c("asin","reviewId","reviewDate","reviewStars")], positive = scorePos, negative = scoreNeg)

#nonzero sentiments
review_sent$reviewStars<-as.numeric(review_sent$reviewStars)
review_sent$sent_sum<-review_sent$positive+review_sent$negative
review_sent$sent_frac<-ifelse(abs(review_sent$positive+review_sent$negative)!=0
                    ,review_sent$sent_sum/abs(review_sent$positive+review_sent$negative),0)

lm.sumout<-lm(formula = review_sent$reviewStars ~ review_sent$sent_sum)
summary(lm.sumout)

#r^2=.12
lm.fracout<-multinom(formula = review_sent$reviewStars ~ review_sent$sent_frac)
summary(lm.fracout)



###Aggregate by asin
review_agg_sent<-sqldf("select asin, reviewDate, sent_sum, (positive+abs(negative)) as abs_sum
        from review_sent group by asin, reviewDate")
