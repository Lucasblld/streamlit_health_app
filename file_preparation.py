#packages used 
import pandas as pd 
from datetime import datetime 
import xmltodict 
from myFunctions import starting_date,get_data,get_dataframe,one_dataframe

#create the rights file with the good info
#right csv file stored in 'right_folder'

nutrition_path = r"D:\Users\lucas\Bureau\project\health_app\raw_files\nutrition.csv"
ios_health = r"D:\Users\lucas\Bureau\project\health_app\raw_files\export.xml"
right_file = r"D:\Users\lucas\Bureau\project\health_app\right_files"

with open(ios_health,errors="ignore") as xmlfile:
    xml = xmltodict.parse(xmlfile.read())

print(xml["HealthData"].keys())
health_data = xml["HealthData"]

df_nutrition = pd.read_csv(nutrition_path)
df_activity = pd.DataFrame(health_data['ActivitySummary'])
df_workout = pd.DataFrame(health_data["Workout"])
df_record = pd.DataFrame(health_data["Record"])

pd.DataFrame(health_data["Me"], index=[0]).to_csv(right_file + '\\me.csv', index=False)
starting_date(df_nutrition, 'Date').to_csv(right_file + '\\nutrition.csv',index=False)
starting_date(df_activity, '@dateComponents').to_csv(right_file + '\\activity.csv',index=False)
starting_date(df_workout, '@creationDate').to_csv(right_file + '\\workout.csv',index=False)
starting_date(df_record, '@creationDate').to_csv(right_file + '\\record.csv',index=False) 

df_nutriton_2 = one_dataframe(pd.date_range('2021-11-21','2021-12-14'))
df_nutriton_2.to_csv(right_file + '\\nutri_2.csv',index=False) 
