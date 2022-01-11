#all packages used
from myFunctions import starting_date, toPyDate,right_data_type,variation,previous_date_generator
from myFunctions import draw_bar_chart
import pandas as pd 
import glob  
import xmltodict
import streamlit as st 
from datetime import datetime, timedelta
from PIL import Image
import plotly.graph_objects as go
import matplotlib.pyplot as plt
import json

#integration of the prepocessing part 

def app(): 

  #reading all files 
  path_csv= r"D:\Users\lucas\Bureau\project\health_app\right_files\*"
  df_activity, df_me, df_ignore, df_nutritions,  df_record, df_workout = [pd.read_csv(file) for file in glob.glob(path_csv)]

  #preprocesing 
  df_feelfit = df_record[df_record["@sourceName"] == "Feelfit"]
  df_feelfit = right_data_type(df_feelfit,df_feelfit.columns)

  #file date/num transformation 

  #sidebar for date selection 
  start_date = st.sidebar.date_input("start_date")
  end_date = st.sidebar.date_input("end_date")

  if start_date <= end_date : 
    st.sidebar.success(f"start date : {start_date}\n\nend date : {end_date}")
  else : 
    st.sidebar.error("You can't have the start date greater than the end date")

  date_range_selector = toPyDate(pd.date_range(start_date, end_date))

  #Creating first main KPIs
  path_man = r"D:\Users\lucas\Bureau\project\health_app\images\man.png"
  path_woman = r"D:\Users\lucas\Bureau\project\health_app\images\woman.png"

  sex, age, height, weight, bodyfat = st.columns(5)

  #sex 
  if df_me['@HKCharacteristicTypeIdentifierBiologicalSex'].str.contains('Male').all()  : 
    image = Image.open(path_man) 
    sex.image(image,width=75)
  else : 
    image = Image.open(path_woman) 
    sex.image(image,width=75)

  #age
  current_age = datetime.now().year - pd.to_datetime(df_me['@HKCharacteristicTypeIdentifierDateOfBirth'])[0].year
  age.metric("Age", current_age)

  #height 
  height.metric("Height in cm", 180)


  #weight & delta 
  #filter
  # list of date test['@creationDate'].dt.date.apply(lambda date: date in [pd.Timestamp('2021-12-14')])
  #last_date = df_feelfit['@creationDate'].dt.date == df_feelfit['@creationDate'].dt.date.max() 
  df_feelfit["date_ref"] = toPyDate(df_feelfit['@creationDate'].to_list())
  last_date = df_feelfit["date_ref"].isin(date_range_selector)

  body_weight = df_feelfit['@type'] == "HKQuantityTypeIdentifierBodyMass"
  weights = df_feelfit[(last_date) & (body_weight)]

  percentage_var = variation(start_date, end_date,df_feelfit, 'date_ref', '@type', "HKQuantityTypeIdentifierBodyMass")
  percentage_var = f'{round(percentage_var, 2)} %'
  weight.metric("weight in KG", round(weights["@value"].mean(),2), delta=percentage_var)

  #fat percentage and delta
  #same note as weight 

  body_fat = df_feelfit['@type'] == "HKQuantityTypeIdentifierBodyFatPercentage"
  last_fat = df_feelfit[(last_date) & (body_fat)]["@value"].mean() * 100

  percentage_fat_var = variation(start_date, end_date, df_feelfit, 'date_ref', '@type', "HKQuantityTypeIdentifierBodyFatPercentage")
  percentage_fat_var = f'{round(percentage_fat_var, 2)} %'
  bodyfat.metric("Fat percentage (%)", round(last_fat,2), delta=percentage_fat_var)

  #create weight comparison graphs
  ref_date=weights["date_ref"].apply(lambda x : x.strftime("%A"))
  previous_date = df_feelfit["date_ref"].isin(previous_date_generator(date_range_selector))
  previous_weight= df_feelfit[(previous_date) & (body_weight)].sort_values("date_ref", ascending=False)
  previous_weight = previous_weight.groupby(["date_ref"])[['@value']].mean().reset_index()
  current_weights = weights.groupby(["date_ref"])[['@value']].mean().reset_index()

  weight_var = draw_bar_chart(["current","previous"],ref_date.unique(), [current_weights["@value"],previous_weight["@value"]])

  #create calories information bar 
  #intake
  df_nutrition_global = df_nutritions.groupby(["Date","meal"]).sum().reset_index()
  df_nutrition_global["Date"] = toPyDate(pd.to_datetime(df_nutrition_global["Date"]).to_list())

  df_nutrition_global_meal = df_nutrition_global.groupby("Date").sum().reset_index()
  nutrition_date_fitler = df_nutrition_global_meal['Date'].isin(date_range_selector)
  colories = df_nutrition_global_meal[nutrition_date_fitler]['calories']

  #burned
  df_activity_global = df_activity.groupby(["@dateComponents"]).sum().reset_index()
  df_activity_global = right_data_type(df_activity_global, df_activity_global.columns)
  df_activity_global["@dateComponents"] = toPyDate(df_activity_global["@dateComponents"].to_list())
  activity_date_fitler = df_activity_global['@dateComponents'].isin(date_range_selector)
  burned = df_activity_global[activity_date_fitler]['@activeEnergyBurned']

  calories_info = draw_bar_chart(['intake','burned'],ref_date.unique(),[colories,burned])

  #nutrients distribution 
  nutrient = df_nutrition_global_meal[nutrition_date_fitler][["fat",'protein','carbohydrates']]
  nutrient_label = nutrient.sum().index
  nutrient_values = nutrient.sum().to_list()

  nutrient_rep = go.Figure(data=[go.Pie(labels=nutrient_label,values=nutrient_values,hole=.5)])

  #top 3 most calorific meals 
  meal_date_fitler = df_nutrition_global['Date'].isin(date_range_selector)
  df_top_cal = df_nutrition_global[meal_date_fitler][["Date","meal", "calories"]].sort_values("calories",ascending=False)
  df_last_cal = df_nutrition_global[meal_date_fitler][["Date","meal", "calories"]].sort_values("calories",ascending=True)

  df_top_cal["meal_info"] =df_top_cal["meal"].head() + " " +df_top_cal["Date"].head().astype(str)
  top_cal_chart = draw_bar_chart(df_top_cal["meal_info"], df_top_cal["calories"].head(), 
                                  [df_top_cal["meal_info"].head()],orientation="h",width=800,height=490)

  df_last_cal["meal_info"] =df_last_cal["meal"].head() + " " +df_last_cal["Date"].head().astype(str)
  bottom_cal_chart = draw_bar_chart(df_last_cal["meal_info"], df_last_cal["calories"].head(), 
                                    [df_last_cal["meal_info"].head()],orientation="h",width=800,height=490)

  bottom_cal_chart.update_layout(xaxis_range=[0,max(df_top_cal["calories"].head()*10//10)])


  # Create Radio Buttons
  display_graph = st.radio(label = 'Graph to display', options= ['weights','calorie intake vs burned','Nutrient'])
  st.write('<style>div.row-widget.stRadio > div{flex-direction:row;}</style>', unsafe_allow_html=True)


  general_graph, meals_info = st.columns([1.4,1])

  if display_graph == 'weights' : 
    weight_var.update_layout(title={
      "text":"Weight Variation in KG",
      "x":0.4,
      'xanchor': 'center',
      'yanchor': 'top',  
    },
    font=dict(size=25))
    general_graph.plotly_chart(weight_var)
  elif display_graph == 'calorie intake vs burned' : 
    calories_info.update_layout(title={
      "text":"Calorie Intake and Burned",
      "x":0.4,
      'xanchor': 'center',
      'yanchor': 'top',  
    },
    font=dict(size=25))
    general_graph.plotly_chart(calories_info)
  else : 
    nutrient_rep.update_layout(title={
      "text":"Nutrient Repartition",
      "x":0.4,
      'xanchor': 'center',
      'yanchor': 'top',  
    },
    font=dict(size=25))
    general_graph.plotly_chart(nutrient_rep)

  # top and bottom calorie meals 
  top_cal_chart.update_layout(title={
      "text":"Top 5 most calorific meals",
      "x":0.4,
      'xanchor': 'center',
      'yanchor': 'top',  
    },
    font=dict(size=15))
  meals_info.plotly_chart(top_cal_chart)

  bottom_cal_chart.update_layout(title={
      "text":"Top 5 les calorific meals",
      "x":0.4,
      'xanchor': 'center',
      'yanchor': 'top',  
    },
    font=dict(size=15))
  meals_info.plotly_chart(bottom_cal_chart)

  #get detail from meal 
  #top_detail_meal, bottom_detail_meal = st.columns([0.5,0.5])

  df_nutritions["meal_info"] = df_nutritions["meal"]+ " " +df_nutritions["Date"].astype(str)

  top_chart_json = top_cal_chart.to_json()
  bottom_chart_json = bottom_cal_chart.to_json()


  meals_selector_top = st.selectbox(
      'which meal would you like to select (more cal)',
      json.loads(top_chart_json)["data"][0]["y"])    

  st.table(df_nutritions[df_nutritions["meal_info"] == meals_selector_top][["name","calories","carbohydrates","fat","protein"]])

  meals_selector_bottom = st.selectbox(
      'which meal would you like to select (less cal)',
      json.loads(bottom_chart_json)["data"][0]["y"])

  st.table(df_nutritions[df_nutritions["meal_info"] == meals_selector_bottom][["name","calories","carbohydrates","fat","protein"]])









