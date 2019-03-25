library(ggplot2)
library(corrplot) #covariance visualization
library(lubridate) # date management
library(zoo) #date management
library(car) #vif detection
library(reshape2) #mdataframe reshape
#setwd("/Users/daniel/Documents/-Work/BeltRoad/")
#self-defined functions####
report_clean <- function(name, time, y){
  #complement for company's missing report, by linear Interpolation
  #for convinience replace 31(days) to 27(days)
  #inpt: name:list of company's name; time: date of report; y: reported value
  #output data.frame： name time y after fix up 
  library(lubridate) # date management
  day(time) <- 27
  name <- as.factor(name)
  #make diff################
  diff_name <- c(F, abs(diff(as.numeric(name))) < 0.5)
  year <- as.numeric(format(time, format='%Y'))
  diff_year <- c(F, diff(year) < 0.5)
  index <- as.numeric(diff_name & diff_year)
  dy <- c(y[1], diff(y))
  y <- dy*index + y*(1-index)
  #seasonal average################
  dmonth <- c(as.numeric(format(time, format='%Y%m')[1]),
              diff(as.numeric(format(time, format='%Y%m'))))
  month <- as.numeric(format(time,format='%m'))
  dseason <- dmonth/3*index + month*(1-index)/3
  y <- rep(y/dseason, dseason)
  name <- rep(name, dseason)
  time <- rep(time, dseason)
  seasonal_index <- rep(dseason, dseason)
  
  index4 <- which(seasonal_index == 4)
  index3 <- which(seasonal_index == 3)
  index2 <- which(seasonal_index == 2)
  index_1 <- c(index2[c(1:length(index2))%%2 == 1],
               index3[c(1:length(index3))%%3 == 2],
               index4[c(1:length(index4))%%4 == 3])
  index_2 <- c(index3[c(1:length(index3))%%3 == 1],
               index4[c(1:length(index4))%%4 == 2])
  index_3 <- c(index4[c(1:length(index4))%%4 == 1])
  
  index_1 <- index_1[!is.na(index_1)]
  index_2 <- index_2[!is.na(index_2)]
  index_3 <- index_3[!is.na(index_3)]
  
  time[index_1] <- time[index_1] - months(3)
  time[index_2] <- time[index_2] - months(6)
  time[index_3] <- time[index_3] - months(9)
  
  de_y <- data.frame(name, time, y)
  return(de_y)
}

Ave <- function(dat, t=1, type='season', ac = F){
  #calculate  the average value among companies for each season
  #t: col index of time，1 by default
  #ac indicates the accumulated value or not. if false calculate avg for each seacon, if true minus previous time period at first.
  library(zoo)
  df <- list()
  if(type == 'season'){time <- as.yearqtr(dat[,t])}
  if(type == 'month'){time <- format(dat[,t], format='%Y-%m')}
  dat <- dat[,c(t,c(1:ncol(dat))[-t])]
  if(ac){
    for(i in 2: ncol(dat)){
      tmp <- aggregate(dat[,i],by=list(time),max, na.rm = T)
      year <- as.numeric(format(tmp[,1], format='%Y'))
      d_year <- as.numeric(c(F, diff(year) < 0.5))
      
      df[[i-1]] <- c(tmp[1,2], diff(tmp[,2]))*d_year + tmp[,2]*(1-d_year)}
  }else{
    for(i in 2: ncol(dat)){
      df[[i-1]] <- aggregate(dat[,i],by=list(time),sum, na.rm = T)[,2] /
        aggregate(dat[,i], by=list(time),
                  FUN = function(x) max(c(1,sum(abs(x) > 0.1, na.rm = T))))[,2]}
  }
  df <- as.data.frame(matrix(unlist(df),nrow=length(df[[1]])))
  df <- cbind(unique(time), df)
  names(df) <- c('time',names(dat)[-1])
  return(df)
}

Model <- function(Y,X, must=c(),vif=15, method=c('aic','adj.r2')){
  #select variables based on arginal-r2, and constarin autocorrelation by vif
  #must: manually selected variables
  #output: $model: the regression model，$index: indice of column that selected in model (Y not counted)
  sst <- var(Y)
  r2 <- c()
  for(i in 1:ncol(X)){
    lm0 <- lm(Y~., data = as.data.frame(cbind(Y,X[,i])))
    tmp <- 1- var(lm0$residuals)/sst
    r2 <- c(r2, tmp)}
  
  index <- must
  if(method == 'aic'){
    aic0 <- extractAIC(lm(Y~., data = as.data.frame(cbind(Y,X[,index]))))[2]
    for(i in order(r2, decreasing = T)){
      if(length(index) == 0){index <- i}
      if(i %in% index) {next}
      lm1 <- lm(Y~., data = as.data.frame(cbind(Y, X[,c(index,i)])))
      if(max(vif(lm1)) > vif){next}
      aic1 <- extractAIC(lm1)[2]
      if(aic1 < aic0){
        index <- c(index,i)
        aic0 <- aic1}}
  }
  if(method == 'adj.r2'){
    lm0 <- lm(Y~., data = as.data.frame(cbind(Y,X[,index])))
    r2_0 <- summary(lm0)$adj.r.squared
    for(i in order(r2, decreasing = T)){
      if(length(index) == 0){index <- i}
      if(i %in% index) {next}
      lm1 <- lm(Y~., data = as.data.frame(cbind(Y, X[,c(index,i)])))
      if(max(vif(lm1)) > vif){next}
      r2_1 <- summary(lm1)$adj.r.squared
      if(r2_1 > r2_0){
        index <- c(index,i)
        r2_0 <- r2_1}}
  }
  
  model <- lm(Y~., data = as.data.frame(cbind(Y, X[,index])))
  return(list(model=model,index=index))
}

#get Y step1 data cleaing####
load('report.rda')
index <- grep('水泥', report$申万二级)
report$report_period <- as.POSIXct(report$report_period, format = '%Y-%m-%d')
cement <- report[index,]

netin <- report_clean(cement$corp_name, cement$report_period, cement$净利润)
netin[netin == 0] <- NA

#get Y step2 group by time####
netin <- netin[order(netin$time),]
netin <- aggregate(netin$y, by=list(as.yearqtr(netin$time)), mean, na.rm = T)
names(netin) <- c('time', 'netin')
# netin

#get X step1 unifrom frequency######
chain <- read.csv('水泥.csv')
names(chain)[1] <- 'time'
chain$time <- as.POSIXlt(chain$time, format = '%Y/%m/%d')

chain_season <- Ave(chain[, -grep('累[积计]', names(chain))], ac=F)
tmp <- Ave(chain[, c(1,grep('累[积计]', names(chain)))], ac=T)
chain_season <- merge(chain_season, tmp, by='time')

#get X step2 omit missing variables####
chain_season <- chain_season[chain_season$time < 2017.5,] #一季度为.0，二季度.25，三季度.5，四季度.75
chain_season[chain_season == 0] <- NA
na1 <- apply(chain_season, 2, function(x){sum(is.na(x))>0.5})
chain_season <- chain_season[,!na1]

#merge X and Y ####
X <- chain_season
#lag variables
X_lag1 <- X
X_lag1$time <- X_lag1$time + 0.25 
names(X_lag1)[-1] <- paste0(names(X)[-1],'_lag1')
X_lag2 <- X
X_lag2$time <- X_lag2$time + 0.5 
names(X_lag2)[-1] <- paste0(names(X)[-1],'_lag2')
X_lag3 <- X
X_lag3$time <- X_lag3$time + 0.75 
names(X_lag3)[-1] <- paste0(names(X)[-1],'_lag3')
X_lag4 <- X
X_lag4$time <- X_lag4$time + 1 
names(X_lag4)[-1] <- paste0(names(X)[-1],'_lag4')

X_all <- merge(merge(merge(merge(X, X_lag1),X_lag2),X_lag3),X_lag4)
y_lag1 <- data.frame(time=netin$time + 0.25, y_lag1=netin$netin)
y_lag2 <- data.frame(time=netin$time + 0.5, y_lag2=netin$netin)
y_lag3 <- data.frame(time=netin$time + 0.75, y_lag3=netin$netin)
y_lag4 <- data.frame(time=netin$time + 1, y_lag4=netin$netin)
X_all <- merge(y_lag1,merge(y_lag2,merge(y_lag3,merge(y_lag4,X_all))))
X_all$season <- as.factor(sub('0','1',quarters(X_all$time))) #to merge seasons into same group

#combine X,Y，save time as t
dat_cement <- merge(netin,X_all)
t <- dat_cement[,1] 
dat_cement <- dat_cement[,-1]

#model#####
m <- Model(dat_cement$netin,
           dat_cement[-1],
           vif=5,
           must = ncol(dat_cement)-1,
           method = 'aic')

mean(abs(m$model$residuals/dat_cement$netin)) #mean of relative error
summary(m$model) 
vif(m$model)

#output####
df <- data.frame(time=t,
                 actual=dat_cement$netin,
                 pred=m$model$fitted.values)
df <- melt(df, id='time')
ggplot(df, aes(time, value, color=variable)) + geom_line() +
  labs(title = 'net income in cement industry')

#save model result and predictions in file
#.csv: true value and fitted value
#.txt: model and prediction

pred <- predict(m$model,X_all[X_all$time == '2017 Q2',m$index+1],se.fit = T,interval = 'confidence')
write.csv(df, file = 'netincome_cement.csv')
sink('model_netincome_cement.txt')
summary(m$model)
m$model$coefficients
print('confidence interval:')
pred$fit
print('standard error:')
pred$se.fit
sink()
