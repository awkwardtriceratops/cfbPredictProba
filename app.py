import numpy as np
import pandas as pd
import requests
import json
import cfbd
import streamlit as st
from pandas import json_normalize
apiKey='7H4eHZRnvnXTUKLltnNusCffvs6YaaLKr1R5gQme50KBHpBDSFkRit7dbUISdAi9'
configuration = cfbd.Configuration()
configuration.api_key['Authorization'] = apiKey
configuration.api_key_prefix['Authorization'] = 'Bearer'
api_instance = cfbd.BettingApi(cfbd.ApiClient(configuration))

# Streamlit app
@st.cache_data
def get_lines():
    api_response=api_instance.get_lines(year=2024,week=9)
    completeDF=pd.DataFrame()
    for i in range(len(api_response)):
        df=pd.DataFrame(api_response[i].to_dict())
        completeDF=pd.concat([completeDF,df])
    lines=json_normalize(completeDF['lines'])
    completeDF = completeDF.drop(columns=['lines']).reset_index(drop=True).join(lines)
    print(completeDF.columns)
    def findImpliedOdds(moneyline):
        if moneyline>0:
            return 100/(moneyline+100)
        else:
            return abs(moneyline)/(abs(moneyline)+100)
    smallDF=completeDF[['away_team','home_team','spread','formatted_spread','home_moneyline','away_moneyline','id']]
    smallDF['aggmoneyline']=abs(smallDF['home_moneyline'])+abs(smallDF['away_moneyline'])
    #find implied odds for home and away
    smallDF['home_implied_odds']=smallDF['home_moneyline'].apply(findImpliedOdds)
    smallDF['away_implied_odds']=smallDF['away_moneyline'].apply(findImpliedOdds)
    smallDF['maxImpliedOdds']=smallDF[['home_implied_odds','away_implied_odds']].max(axis=1)
    smallDF.sort_values(by='maxImpliedOdds',ascending=False,inplace=True)
    smallDF.reset_index(drop=True,inplace=True)
    def findFavorite(row):
        if row['home_moneyline']<row['away_moneyline']:
            return row['home_team']
        else:
            return row['away_team']
    smallDF['favorite']=smallDF.apply(findFavorite,axis=1)
    displayDF=smallDF.groupby(['home_team','away_team','favorite','id']).agg({'aggmoneyline':'mean','maxImpliedOdds':'mean','home_implied_odds':'mean','away_implied_odds':'mean'}).sort_values(by='maxImpliedOdds',ascending=False)
    #pull the odds from the metrics
    api_instance_3=cfbd.MetricsApi(cfbd.ApiClient(configuration))
    prob=api_instance_3.get_pregame_win_probabilities(year=2024,week=9) 
    probDF=pd.DataFrame()
    for game in prob:
        probDF=probDF._append(game.to_dict(),ignore_index=True)
    #merge on gameid
    print(displayDF.columns)
    displayDF=displayDF.reset_index().merge(probDF[['game_id','home_win_prob']],left_on='id',right_on='game_id')
    displayDF['value']=displayDF['home_win_prob']-displayDF['home_implied_odds']
    displayDF.sort_values(by='value',ascending=False,inplace=True)  
    return displayDF
st.header('CFB Betting Lines versus Probabilities')
st.write(get_lines())