library(plyr)
library(rmongodb)
library(dplyr)
library(sqldf)
library(ggplot2)
library(lattice)


token_counts <- read.csv('/home/hadoopuser/Documentos/text_mining/data/token_counts.csv')

names(token_counts)
item_dtm <- read.csv('/home/hadoopuser/Documentos/text_mining/data/item_dtm.csv')
meta_drill_info <- read.csv("/media/jupiter/hadoopuser/data/meta_drills.csv")




#get from analysis_prices_collapsed file!!!
reviews<- sqldf("select a.* , c.maxprice, c.price_group_long
                from reviews2 as a 
                left  join max_price as c
                on a.asin = c.asin")
reviews_token_count <- sqldf("select a.* , c.tokenLength
                from reviews as a 
                left  join token_counts as c
                on a.reviewId = c.reviewId")

hist(reviews_token_count$tokenLength[reviews_token_count$tokenLength<200&reviews_token_count$tokenLength>0],
     main="# of Tokens Per Review", xlab="Number of Tokens", breaks=100)


hist(reviews_token_count$tokenLength[reviews_token_count$tokenLength<200],
     main="# of Tokens Per Review", xlab="Number of Tokens")


my.settings <- canonical.theme(color=FALSE)
my.settings[['strip.background']]$col <- "black"
my.settings[['strip.border']]$col<- "black" 
histogram( ~ tokenLength | price_group_long, data=reviews_token_count[reviews_token_count$tokenLength<200,], type = c("count"), 
           par.settings = my.settings, par.strip.text=list(col="yellow", font=2),
           scales=list(y=list(relation="free")),
           main="Frequency of Review Tokens \n by Product Price", xlab="# of review tokens")

histogram( ~ tokenLength | as.factor(reviewStars), data=reviews_token_count[reviews_token_count$tokenLength<200,], type = c("count"), 
           par.settings =my.settings, par.strip.text=list(col="yellow", font=2),
           scales=list(y=list(relation="free")),
           main="Frequency of Review Tokens \n by Review Star Rating", xlab="# of review tokens")



