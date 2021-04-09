import pandas as pd
import numpy as np
import yfinance as yf
import scipy.stats as scipy

start='2019-01-01'                                      # UPDATE START DATE FOR DATA ANALYSIS ; RECOMMENDED 500 DAYS DATA
path= 'C:/Users/XXXX/Documents/'                        #UPDATE LOCATION TO READ THE STOCK LIST FILE AND SAVE FINAL OUTPUT
stocklist= 'nse100list.csv'                                  # NAME OF THE STOCK LIST FILE FOR WHICH PAIR TRADING TO BE TESTED 
stockpricedata='stockpricedata.csv'
complete_cal_dump='complete_cal_dump.csv'
final_signal='final_signal.csv'

x=pd.read_csv(path+stocklist)
stocks=x['Symbol'].to_list()
stocks=stocks[1:101]                                    # Change index to match with no of securities in the stock list file

if input("Do you want to download latest data:").upper() == 'Y':     
    data=[]
    for stock in stocks:
        download=yf.download(stock,start)
        download=download.dropna()
        data.append(download['Close'])

    stockdata=pd.DataFrame(data).transpose()
    stockdata.columns=stocks
    stockdata.to_csv(path+stockpricedata)

stockdata= pd.read_csv(path+stockpricedata, index_col='Date')

returndata=pd.DataFrame()

#----------------------------FINDING CORRELATION ---------------------------
for column in stockdata.columns:
    returndata['return_'+column]=(stockdata[column].pct_change())*100

corrlist=[]
ratiolist=[]
corr=[]
i=0
while i<len(stocks):
    for column in returndata.columns[i:len(stocks)]:
        x=returndata['return_'+stocks[i]].corr(returndata[column])
        if x > 0.75 and x!=1.0:                                           #Change Correlation parameter here!
            corrlist.append(stocks[i])
            corrlist.append(column[7:])
            ratiolist.append(stocks[i]+' / '+column[7:])
            corr.append(x)
    
    i +=1

corrlist=list(set(corrlist))
densitylist=['Density_'+x for x in ratiolist]
finallist=corrlist+ratiolist+densitylist

stockdata=stockdata[corrlist].T.drop_duplicates().T
corrdata=pd.DataFrame(list(zip(ratiolist,corr)), columns=['Pair','Corr'])

#-------------------------------RATIO OF SHARES AGAINST EACH OTHER & SELECTING RELEVANT COLUMNS ONLY----------------------
i=0
while i<len(corrlist):
    for column in stockdata.columns[:len(corrlist)]:
        stockdata[corrlist[i]+' / '+column]=stockdata[corrlist[i]]/stockdata[column]
        stockdata['Density_'+corrlist[i]+' / '+column]= scipy.norm.cdf(stockdata[corrlist[i]+' / '+column],stockdata[corrlist[i]+' / '+column].mean(),\
                       stockdata[corrlist[i]+' / '+column].std())
    i +=1

stockdata=stockdata[finallist]    

#********************************************logic for trade********************************************
#Pair trade logic (density between +/- 2 and 3 SD ; SL @ 3 SD ; TP @ 1 SD):
    # 0.003 < Pair density < 0.025 : Long Pair with Target density >=0.32 and Stop Loss Density < 0.003
    # 0.975 < Pair density < 0.997 : Short Pair with Target density <= 0.68 and Stop Loss Density > 0.997

#------------------------------------ FINDING DENSITY FUNCTION---------------------------------------------

pair=[]
ratio=[]
cdf=[]
signal=[]
for column in stockdata.columns:    
     if 'Density' in column:
            if stockdata[column][-1] < 0.025:                     #change the value of cdf as per logic above
                pair.append(column[8:])
                ratio.append(stockdata[column[8:]][-1])
                cdf.append(stockdata[column][-1])
                signal.append("Long pair")
            elif stockdata[column][-1] > 0.975:                  #change the value of cdf as per logic above
                pair.append(column[8:])
                ratio.append(stockdata[column[8:]][-1])
                cdf.append(stockdata[column][-1])
                signal.append("Short pair")


final=pd.DataFrame(list(zip(pair,ratio,cdf,signal)), columns=['Pair','Ratio','CDF','Signal'])
final=corrdata.merge(final,on='Pair').set_index('Pair')

final.to_csv(path+final_signal)                                 # E.g. FOR A / B pair In the signal file long pair means long A and short B 
stockdata.to_csv(path+complete_cal_dump) 
