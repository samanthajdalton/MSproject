library(plyr)
library(sqldf)
library(latticeExtra)
library(rmongodb)
library(dplyr)
library(ggplot2)
library(lattice)
options(digits=2)
library(scales)

###Data Path
path<-'/media/jupiter/hadoopuser/amazon/data/'

#######################    PRICES    #############################################
'''
READING in prices from Tracktor (ideally do this with rmongodb,
but I did a data dump from mongodb to csv to make faster progress )
Ideally this pricing data would come from Amazon and would inslude sales rank
'''

  #Read in price data
  prices <- read.csv(paste0(path,'drill_prices_table.csv'), header=T)

  #Read in product info 
  meta_drill_info <- read.csv(paste0(path,"meta_drills.csv"))

  prices$date <- strptime(prices$date,"%Y%m%d")
  prices <- prices[order(prices$asin,prices$date),]
  
  #Create lag date and price
  prices$date <- as.Date(prices$date)
  prices <- prices[!is.na(prices$priceNew),]
  
  #Get lagged price by product
  prices2 <- prices %>%
    group_by(asin) %>% select(-priceUsed) %>%
    mutate(lagPriceNew = lag(priceNew, 1), lagDate=lag(date,1)) 
  
  #Get rid of really tiny price changes (less than 17 cents)
  delete_flag <- ifelse (!(prices2$lagDate==prices2$date & (abs(prices2$lagPriceNew-prices2$priceNew)<0.17)),0,1)
  delete_flag <- delete_flag
  delete_flag[is.na(delete_flag)] <- 0
  prices2$delete_flag <- delete_flag
  Q <- prices2[prices2$delete_flag != 1,]
  R <- Q[order(Q$asin,Q$date),]
  prices2 <- R %>%
    group_by(asin) %>% 
    mutate(lagPriceNew = lag(priceNew, 1), lagDate=lag(date,1)) 
  
  
  #Calculate price percentage change from lagged price and other lagged value differences
  PctChange <- (prices2$priceNew-prices2$lagPriceNew) / prices2$lagPriceNew
  prices2$PctChange <- PctChange
  prices2$date_diff <- as.numeric(prices2$date - prices2$lagDate)
  prices2$price_diff <- prices2$priceNew-prices2$lagPriceNew
  prices2$lagDate[is.na(prices2$lagDate)] <- as.Date('08-01-2012','%m-%d-%Y')

  #Raw distribution of price changes
  hist(prices2$PctChange[prices2$PctChange<1],breaks=100, main='Histogram of Price Changes \n before Data Cleaning', xlab='%change')
  
  #Cleaning prices to only take the largest absolute price change for the day (istead of multiple recorded zero changes)
  pricesClean <- sqldf("select asin, date, priceNew, lagPriceNew, lagDate, price_diff, date_diff, 
                      max(abs(price_diff)) as mpd from prices2 
                      group by asin, date having max(abs(price_diff))
                      order by asin, date  ")

  #Calculating price % change from lagged value
  pctChange <- (pricesClean$priceNew - pricesClean$lagPriceNew) / pricesClean$lagPriceNew
  pricesClean$pctChange <- pctChange
  pricesClean <- pricesClean[order(pricesClean$asin,pricesClean$date),]
  
  asins <- as.vector(unique(prices$asin))
  
  #determining if if price changes are iid across prices of products
  summary(lm(pctChange~priceNew, data=pricesClean))
  ggplot(pricesClean[pricesClean$pctChange<1&pricesClean$pctChange!=0,], aes(priceNew,pctChange)) + geom_point(alpha=0.2,shape=1)+theme_bw() + geom_abline(intercept=-0.0076, slope=0.00012)
  
  #only keeping observations where the lag price is available
  prices2 <- pricesClean
  delete_flag[is.na(delete_flag)] <- 0
  prices2$price_diff[is.na(prices2$price_diff)] <- 0
  

#Smoothing out the pricing data using business rules to get rid of flash sales
  pricesClean2 <- c()
  for (i in 1:length(asins)) {    
    temp <- prices2[prices2$asin == asins[i],] 
    
    if (is.data.frame(temp)){
      temp$deleteFlag <- 0
      #loop through price dates for the product
      for (j in 1:nrow(temp)) {
        #if it's the first product, don't delete the obs
        if (j==1 ){
          temp$deleteFlag[j] <- 0
          
        #if it's after the first date, delete the obs if there are <5 days and an abs price change < 18 cents
        #since the the lagged date
        } else if  (temp$date_diff[j] <= 5 & abs(temp$price_diff[j]) < 0.18){          
          temp$deleteFlag[j] <- 1
          
        #take care of flash sales-delete obs if the lagged value was exaclty the opposite amount and it was within 2 days
        }    else if ( temp$date_diff[j] <= 2 & round(temp$price_diff[j]) == -round(temp$price_diff[j-1])){
          temp$deleteFlag[j] <- 1
          temp$deleteFlag[j-1] <- 1
        }
      }
      pricesClean2 <- rbind(pricesClean2,temp[temp$deleteFlag==0,])
    }
  }
  
  
  #Create the lagged priced values on the clean data
  pricesClean2 <- pricesClean2[order(pricesClean2$asin,pricesClean2$date),]
  pricesClean3 <-  pricesClean2 %>%
                   group_by(asin) %>% 
                   mutate(lagPriceNew = lag(priceNew, 1), lagDate = lag(date,1)) 
    
  #Create new lag differences
  PctChange <- (pricesClean3$priceNew-pricesClean3$lagPriceNew) / pricesClean3$lagPriceNew
  pricesClean3$PctChange <- PctChange
  pricesClean3$date_diff <- as.numeric(pricesClean3$date - pricesClean3$lagDate)
  pricesClean3$price_diff <- pricesClean3$priceNew - pricesClean3$lagPriceNew
  pricesClean3$pctChange <- NULL

  #Histograms summarizing  prices % changes on the cleaned data
    hist(pricesClean3$PctChange[pricesClean3$PctChange<1],breaks=100, main='Histogram of Price Changes \n after Data Cleaning ', xlab='%change')
    hist(pricesClean3$PctChange[pricesClean3$PctChange<1&pricesClean3$PctChange!=0],
         breaks=100, main='Histogram of Price Changes after Data Cleaning \n 0% NOT included ', xlab='%change')
    hist(as.numeric(pricesClean3$price_diff), breaks=50, main="Dollar Difference"
    hist(as.numeric(pricesClean3$date_diff[pricesClean3$date_diff<100]), breaks =50,
        xlab="Difference in Days Since Last Review", main="Number of Days Between Reviews")
       
       
       
       
      #Getting the maximmum product price in order to assign products to product price groups 
       max_price <- sqldf("select asin , max(priceNew) as maxprice
                         from pricesClean3 group by asin ")  
       
       price_group <- ifelse(max_price$maxprice<50, "A",
                            ifelse(max_price$maxprice >= 50 & max_price$maxprice < 100, "B", 
                                   ifelse(max_price$maxprice >= 100 & max_price$maxprice < 150, "C","D")))
       price_group_long <- factor(price_group, levels=c('A','B','C','D'), labels=c("<$50", "$50-$100","$100-$150","$150-$200"))
       
       max_price$price_group <- price_group
       max_price$price_group_long <- price_group_long
       
       #Adding in product age and price to % change data
       pricesClean4 <- sqldf("select a.*, b.price_group, b.price_group_long, b.maxprice, c.age
                            from pricesClean3 as a 
                            left join max_price as b
                            on a.asin = b.asin
                            left join meta_drill_info as c
                            on a.asin = c.asin")  
       
       table(max_price$price_group_long)
       
       
       nonzero_pchanges <- pricesClean4[complete.cases(pricesClean4) & pricesClean4$PctChange!=0 & pricesClean4$PctChange<=1 & pricesClean4$date >='2013-01-01' ,]
        
       
       pchanges_product_age<-sqldf("select asin, count(*) as count_pchange, age 
                                   from nonzero_pchanges group by asin ")
      
       sqldf("select count(*),avg(PctChange), price_group_long from pricesClean4
             group by price_group_long")
    
      #Analysis of distributions by price group
      table(pricesClean4$price_group_long)
      summary(lm(PctChange~priceNew,data=nonzero_pchanges))
      ggplot(nonzero_pchanges, aes(priceNew,PctChange)) + geom_point(alpha=0.2,shape=1)+theme_bw() + geom_abline(intercept=-0.03159, slope=0.000365)
      
      summary(lm(count_pchange~age,data=pchanges_product_age[pchanges_product_age$count_pchange<90,]))
      plot(pchanges_product_age$age,pchanges_product_age$count_pchange, main="Count of Non-zero price changes by Product Age", xlab="Product Age Days", ylab="Number of Price Changes")

       #make histograms of price % change by price groups
       my.settings <- canonical.theme(color=FALSE)
       my.settings[['strip.background']]$col <- "black"
       my.settings[['strip.border']]$col<- "black" 
       print(histogram( ~ PctChange[abs(PctChange)<=1] | price_group_long, data=pricesClean4[PctChange!=0,], type = c("count"), par.settings = my.settings, par.strip.text=list(col="yellow", font=2),main="Frequency of Price Percentage Changes \n by Product Price", xlab='% Price Change \n (zero price changes NOT included)'))
       
    
      ####Analyze price changes by day of week
      pricesClean4$weekday<-weekdays(pricesClean4$date)
      ddply(pricesClean4, .(weekday), summarize, mean=mean(PctChange, na.rm=TRUE), median=median(PctChange, na.rm=TRUE), n=length(PctChange))
      #Mean price change by day
      ddply(pricesClean4[pricesClean4$PctChange!=0,], .(weekday), summarize, mean=mean(PctChange, na.rm=TRUE), median=median(PctChange, na.rm=TRUE), n=length(PctChange))
      
      
      xyplot(PctChange ~ date, pricesClean4[pricesClean4$date>'2013-01-01',] , 
             ylab="Price", type = "p", group=weekday, auto.key=list(space="top", columns=2,  title="Day", cex.title=1,  lines=TRUE,points=FALSE))
      
     
################ REVIEWS AND PRODUCT META INFO ##################################       
     reviews<-read.csv(paste0(path,'drill_reviews_table.csv'))
  head(reviews)     

     reviews$date<-gsub(",","",as.character(reviews$reviewDate))
     reviews$date<-as.Date(reviews$date, format=" %B %e %Y")
     
     #getting info on previous reviews/ lagged reviews
     reviews<-reviews[order(reviews$asin,reviews$date),]
     reviews2 <- reviews %>%
       group_by(asin) %>%
       mutate(lag_reviewStars = lag(reviewStars, 1), lag_date=lag(date,1))
     
     date_diff <- abs(reviews2$date-reviews2$lag_date)     
     reviews2$date_diff <- as.numeric(date_diff)
     
     #Getting product age information
     meta_drill_info$dateFirstAvailable<-gsub(",","",as.character(meta_drill_info$dateFirstAvailable))
     meta_drill_info$dateFirstAvailable<-as.Date(meta_drill_info$dateFirstAvailable, format=" %B %e %Y")
     age<-Sys.Date()-meta_drill_info$dateFirstAvailable
     meta_drill_info$age<-as.numeric(age)
     

   #Joining product age and price infor to review information
    reviews<- sqldf("select a.* , b.age, c.maxprice, c.price_group_long
                     from reviews2 as a 
                     left join meta_drill_info as b 
                     on a.asin=b.asin
                     left  join max_price as c
                     on a.asin = c.asin")
    
     #335 > 100days and 1.3k>30days, 111 NA
     

     #Plots / Analysis of review frequency
     hist(reviews2$date_diff[reviews2$date_diff<=30], breaks=30)
    
     plot(reviews$age, reviews$date_diff, main="Product Age vs Review Frequency ",
          xlab="Age (days) ", ylab="(days b/w reviews ", pch=1) 

     test<-reviews[reviews$date>'2012-06-01'& reviews$date_diff<650,]
     plot(test$age, test$date_diff, main="Product Age vs Review Frequency \n (Reviews after June 2012) ",
          xlab="Age (days) ", ylab="Days b/w reviews ", pch=1) 
     
     
     my.settings <- canonical.theme(color=FALSE)
     my.settings[['strip.background']]$col <- "black"
     my.settings[['strip.border']]$col<- "black" 
     histogram( ~ reviewStars | price_group_long, data=reviews, type = c("count"), par.settings = my.settings, par.strip.text=list(col="yellow", font=2),main="Frequency of Review Stars \n by Product Price", xlab="Review Stars")
     
####Creating cumulated review information for each new review for a product     
     asins <- sapply(meta_drill_info$asin, as.character)
     reviews_cum <- c()
     for (i in 1:length(asins)){       
       sub_asin <- reviews[reviews$asin==asins[i],]
       for(j in 1:nrow(sub_asin)){
      #if first review set all info to 0
         if (j==1){
           sum_Stars <- 0
           max_star <- 0
           min_star <- 5
         }      
         sub_asin$reviewCount[j]  <- j
         sum_Stars <- sum_Stars + sub_asin$reviewStars[j]
         sub_asin$avg_reviewStars[j] <-  sum_Stars /j
         min_star <- min(min_star,sub_asin$reviewStars[j])
         sub_asin$min_star[j] <- min_star
         max_star <- max(max_star,sub_asin$reviewStars[j])
         sub_asin$max_star[j] <- max_star
         
       }
       reviews_cum <- rbind(reviews_cum,sub_asin)
     }
    #add in lagged values for max, min and avg review star    
     reviews_cum <- reviews_cum[order(reviews_cum$asin,reviews_cum$date),]
     review_cum2 <- reviews_cum %>% group_by(asin) %>%
                    mutate(lag_reviewCount = lag(reviewCount, 1), 
                           lag_avg_reviewStars=lag(avg_reviewStars,1),
                            lag_min_star=lag(min_star,1),
                            lag_max_star=lag(max_star,1))
     
     
     #cumulated counts and lag by asin,date
     reviews_dates <- sqldf("select *  from  review_cum2 
                       group by asin, date
                      having max(reviewCount)")
   
     

    #Get the latest set of review information to occur before the first price in our data
    minmax_date <- sqldf("select asin, min(date) as minDate, max(date) as maxDate from
                   pricesClean4  where date !=15693 group by asin ")

    #if more than 1 review on same day, take the last review (one with highest fum count))
    review_cum3 <- sqldf("select *, asin as asinId, date as date2  from  review_cum2 
                       group by asin, date
                      having max(reviewCount)")

    review_cum3$date2 <- as.Date(review_cum3$date2, origin = "1970-01-01")
    #drop these vars so we don't have multiple vars with same name in sql
    review_cum3$asin <- NULL
    review_cum3$date <- NULL




##### MAKE  DAILY PRICING TEMPLATE FOR EACH PRODUCT ##########

  #Get list of all product ids
  asins <- sapply(minmax_date$asin, as.character)
  
  #Making data frame to have prices of the good available every day
  for (i in 1:length(asins)){
    if (i==1){
      dateTemplate <- c()
      dateFrame3 <- c()
    }
    asin <- asins[i]
    #Get products min and max price date info
    mm_date <- minmax_date[minmax_date$asin==asins[i],]
    prices <- pricesClean4[pricesClean4$asin==asins[i],]
    minDate <- min(mm_date$minDate)
    maxDate <- min(mm_date$maxDate)
    #Create a sequence of dates for everyday between min and max price date info
    dates <- as.Date(seq(minDate,maxDate),origin= "1970-01-01")
    asinId <- rep(asin, length(dates))
    dateFrame <- data.frame(asinId,dates)
    #Combine dateframe work with prices available from traktor
    dateFrame2 <- sqldf("select a.asinId as asin, a.dates as date, b.priceNew
                      from dateFrame as a
                      left join prices as b
                      on a.dates = b.date")
    
    #get cumulative review ids for the product
    revCum <- review_cum3[review_cum3$asinId==asins[i],]
    
    #select the cumulative review info for the review associated right before or on the first date price is available
    minRev$min <- ifelse (!all(is.na(revCum[revCum$date2 < as.Date(min(mm_date$minDate),origin= "1970-01-01"),]$date2)),
                   as.Date(max(revCum[revCum$date2< as.Date(min(mm_date$minDate),origin= "1970-01-01"),]$date2),origin= "1970-01-01"),
                   as.Date(min(revCum$date2),origin= "1970-01-01"))
   
    #Combine price frame work and the cumulated info
    dateFrame3 <- sqldf("select a.*, b.*
                       from dateFrame2 as a 
                       left join revCum as b
                       on a.asin=b.asinId and a.date=b.date2")
    
    #Looking for new prices and updating each day's price template to either new value or previous price if no change
    price <- rep(0, nrow(dateFrame3))
    for (j in 1:nrow(dateFrame3)){
      #if a price exists for the day, put it in the framework
      if (!is.na(dateFrame3$priceNew[j])){
          price[j] <- dateFrame3$priceNew[j]  
      #otherwise, use previous day's price
      } else {
          price[j] <- price[j-1] 
          
      }
      ####Looking for new review information and updating accordingly so that every day in the template has some review information
      #first day of reviews gets info associated with review info right before first day of prices
      if (is.na(dateFrame3$reviewStars[j])& j==1){
        dateFrame3$reviewCount[j] <- revCum[revCum$date2==as.Date(minRev$min,origin='1970-01-01'),]$reviewCount
        dateFrame3$reviewStars[j] <- revCum[revCum$date2==as.Date(minRev$min,origin='1970-01-01'),]$reviewStars
        dateFrame3$avg_reviewStars[j] <- revCum[revCum$date2==as.Date(minRev$min,origin='1970-01-01'),]$avg_reviewStars
        dateFrame3$min_star[j] <- revCum[revCum$date2==as.Date(minRev$min,origin='1970-01-01'),]$min_star
        dateFrame3$max_star[j] <- revCum[revCum$date2==as.Date(minRev$min,origin='1970-01-01'),]$max_star
      }
      #if review info isn't available for that day, use previous day's cumulative review info
      if (is.na(dateFrame3$reviewStars[j])& j!=1){
        dateFrame3$reviewStars[j] <- dateFrame3$reviewStars[j-1]
        dateFrame3$reviewCount[j] <- dateFrame3$reviewCount[j-1]
        dateFrame3$avg_reviewStars[j] <- dateFrame3$avg_reviewStars[j-1]
        dateFrame3$min_star[j] <- dateFrame3$min_star[j-1]
        dateFrame3$max_star[j] <- dateFrame3$max_star[j-1]
      }
    }
    dateFrame4 <- cbind(dateFrame3,price)
    dateTemplate <- rbind(dateTemplate,dateFrame4)
  }  
    
  dateTemplate2 <- dateTemplate %>% 
                  select(-c(lag_reviewCount, lag_avg_reviewStars, age, date_diff, lag_date, lag_reviewStars, 
                            date2, asinId, lag_max_star, lag_min_star, reviewDate, reviewId, priceNew))
  

############Create correlations for different sized review windows######  
    #Looping through windows to see if prices or review stars have changed
    get_corrs<- function (rWindow){
        for (i in 1:length(asins)) {
          if (i==1) {
            modelling<-c()
          }
          
          asin <- asins[i]
          prices<- dateTemplate2[dateTemplate2$asin==asins[i],]
          
          #set up new vectors same length as price template framework
          newReviewCounts <- c(rep(NA,nrow(prices)))    
          windowPctChange <- c(rep(NA,nrow(prices)))
          minStarChange <- c(rep(NA,nrow(prices)))
          maxStarChange <- c(rep(NA,nrow(prices)))
          avgStarChange <- c(rep(NA,nrow(prices)))
          
          #use only records tha are +1 day after the review window size (otherwise will get NAs)
          if (nrow(prices)>(rWindow+1)){
            for (d in (rWindow+1):nrow(prices)) {
                    #compute the price and rating difference from the current date and the date at
                    #the beginning of the window
                    newReviewCounts[d] <- prices$reviewCount[d] - prices$reviewCount[d-rWindow]                       
                    windowPctChange[d] <- (prices$price[d] - prices$price[d-rWindow]) / prices$price[d-rWindow]
                    minStarChange[d] <- prices$min_star[d] - prices$min_star[d-rWindow]
                    maxStarChange[d] <- prices$max_star[d] - prices$max_star[d-rWindow]
                    avgStarChange[d] <- prices$avg_reviewStars[d] - prices$avg_reviewStars[d-rWindow]
                          
              }
            
              prices2<-cbind(prices, newReviewCounts,  windowPctChange,  minStarChange,
                              maxStarChange, avgStarChange)
               modelling<-rbind(modelling,prices2)
          }
      }
      
      d2<-modelling[(modelling$avgStarChange!=0 & modelling$windowPctChange!=0 ),]
      #Get correlation between price % change and star rating change for review window period
      corrVec<- c(rWindow,cor(d2$windowPctChange, d2$avgStarChange, use="complete.obs"), cor(modelling$windowPctChange, modelling$avgStarChange, use="complete.obs"))
      return(corrVec)
    }
    
  
  
  #### Run Tests on review window size
  windows <-seq(1,65,1)
  ##Loop over review windows from 1 to 65 days and calculate correlations (TAKES A WHILE TO RUN)
  correlations<-c()
  for (i in 1:length(windows)){
    corr <- get_corrs(windows[i])
    print(corr)
    correlations <- rbind(correlations,corr)
    
  }
  
#Create data frame from correlations created by looping over different review window sizes
  correlations <- data.frame("window"=correlations[,1], "corr_nonZero"=correlations[,2], "corr_all"=correlations[,3])

##Plot results
  plot_corrs <- ggplot(correlations, aes(window)) + geom_line(aes(y = corr_nonZero), color='Red', label="Excludes Days with No New Reviews AND 0% price changes") + 
        geom_line(aes(y = corr_all)) + theme_bw() + theme(legend.position = "none") +
        geom_text(aes(30,0.08,label="Days with No New Reviews AND 0% Price Change Excluded",size=1, color="Red"))+
        geom_text(aes(25,0,label="Days with No New Reviews AND 0% Price Change Included", size=1))+
        ylab("Correlation") + xlab("Days before Price Capture") + 
    ggtitle("Correlation between Review Changes \n and Price Changes by Review Window ")
  plot_corrs
