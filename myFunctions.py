####################### packages used #######################
from datetime import timedelta 
import pandas as pd 
import numpy as np 
import plotly.graph_objects as go
import myfitnesspal
import json
import matplotlib.pyplot as plt 
from matplotlib import cm


##################### API #######################
def get_data(dates_): 
      """get_raw data from myfitnesspal API"""

      client = myfitnesspal.Client('*******', password='*********')
      breakfast = [client.get_date(date_).meals[0] for date_ in dates_]
      lunch = [client.get_date(date_).meals[1] for date_ in dates_]
      dinner = [client.get_date(date_).meals[2] for date_ in dates_]
      snack = [client.get_date(date_).meals[3] for date_ in dates_]

      return breakfast,lunch,dinner,snack


def get_dataframe(meals,dates_): 
      """transform raw data from myfitnesspal into dataframe"""

      dfs = [pd.DataFrame(meal.get_as_list()) for meal in meals]

      for df, date_ in zip(dfs,dates_): 
            df['Date'] = date_

      df_raw = pd.concat(dfs)
      df = df_raw['nutrition_information'].apply(pd.Series)
      df = pd.concat([df_raw,df],axis=1).reset_index()
      df = df.drop(columns=["nutrition_information","index"])

      return df 

def one_dataframe(all_date): 
      """add type to meal and build the entire datatrame"""

      meals = get_data(all_date)
      all_meals = [get_dataframe(meal,all_date) for meal in meals]
      breakfast, lunch, dinner, snack = all_meals
      
      breakfast['meal'] = "breakfast"
      lunch['meal'] = "lunch" 
      dinner['meal'] = "dinner"
      snack['meal'] = "snack"

      return pd.concat([breakfast,lunch,dinner,snack])

####################### preprocessing and computation #######################

def starting_date(df,col, start_date='2021-11-21'): 
  '''Scope for the analysis.  wrong data before that date''' 

  return df[df[col] >= start_date]

def toPyDate(list_): 
      """convert date like data as native python datetime""" 

      return [date_.to_pydatetime().date() for date_ in list_]


def right_data_type(df, columns) : 
      """convert date to datime and object to float put info fot dataframes"""

      for col in columns : 
            try :
                  df[col] = df[col].astype(float) 
            except : 
                  pass 

      for col in columns : 
            if df[col].dtype != float : 
                  try :
                        df[col] = pd.to_datetime(df[col]) 
                  except : 
                        pass

      return df


def previous_date_generator(date_list): 
      '''get date - n from a date'''

      n = len(date_list)
      return [date_ - timedelta(7) for date_ in date_list]


def variation(start,end,df,col_date,col,col_info):
      """ general case of calculating variation"""

      current_dates = toPyDate(pd.date_range(start, end))
      previous_dates = previous_date_generator(current_dates)

      current = df[col_date].isin(current_dates)
      previous = df[col_date].isin(previous_dates)

      info = df[col] == col_info

      x_0 = df[(current) & (info)]["@value"].mean()
      x_1 = df[(previous) & (info)]["@value"].mean()

      return ((x_0 - x_1)/x_1)*100


####################### Visualisation #######################
def draw_bar_chart(name_list, x_axis, y_axis,orientation="v",width=1000,height=1000):
      """plot bar chart single or grouped"""
   
      data = [go.Bar(name=name,x=x_axis,y=y,orientation=orientation) for 
          name,y in zip(name_list,y_axis)]

      fig = go.Figure(data=data)
      #fig.update_layout(barmode='group')
      #fig.update_layout(yaxis_categoryorder ='total ascending')
      fig.update_layout(autosize=False,width=width,height=height)

      return fig

def draw_radial_bar(categories_, percent_) : 

      categories = categories_
      data = percent_

      percent_circle_cal = data[0] / 700
      percent_circle_time = data[1] / 60
      #number of data points
      n = len(data)
      #find max value for full ring

      #radius of donut chart
      r = 1.5
      r_inner = 0.4
      #calculate width of each ring
      w = (r - r_inner) / n

      #create colors along a chosen colormap
      colors = cm.tab10.colors

      #create figure, axis
      fig, ax = plt.subplots(figsize = (6,3))
      ax.axis("equal")

      #create rings of donut chart
      innerring, _ = ax.pie([700 - data[0], data[0]], radius = r - 0 * w, startangle = 90, counterclock=True,
                        labeldistance = None, colors = ["white", colors[3]],wedgeprops={'width': w, 'edgecolor': 'white'})
      plt.setp(innerring, width = w, edgecolor = "white")

      ax.text(0, r - 0 * w - w / 2, f'{categories[0]} - {round(percent_circle_cal,2)*100}% ', ha='right', va='center')

      innerring, _ = ax.pie([60 - data[1], data[1]], radius = r - 1 * w, startangle = 90, counterclock=True,
                        labeldistance = None,  colors = ["white", colors[1]],wedgeprops={'width': w, 'edgecolor': 'white'})
      plt.setp(innerring, width = w, edgecolor = "white")
      ax.text(0, r - 1 * w - w / 2, f'{categories[1]} - {round(percent_circle_time,2)*100}% ', ha='right', va='center')

      ax.spines.clear()
      plt.tight_layout()

      return plt

def draw_scatter_plot(heart_date,heart_rate,recovery_date,recovery_rate) : 

      fig = go.Figure()

      fig.add_trace(
      go.Scatter(x=list(heart_date),y=list(heart_rate),
            name='Heart Rate',mode='markers'))

      fig.add_trace(
      go.Scatter(x=list(recovery_date),y=list(recovery_rate),
            name='Heart Rate Recovery'))

      #title 
      fig.update_layout(
      title_text = 'Heart Rate Variation',
      title_x=0.5
      )
      
      #range slider 
      fig.update_layout(
      xaxis=dict(
            rangeselector=dict(
                  buttons=list([
                              dict(count=7,
                                    label='7 min',
                                    step='minute',
                                    stepmode='backward'),
                              dict(count=15,
                                    label="15 min",
                                    step='minute',
                                    stepmode='backward'),
                              dict(step='all')
                  ])
            ),
            rangeslider=dict(visible=True)
      ),
      )

      return fig