#packages used 
from myFunctions import starting_date, toPyDate,right_data_type,variation,previous_date_generator
from myFunctions import draw_bar_chart,draw_radial_bar,draw_scatter_plot
import pandas as pd 
import glob  
import xmltodict
import streamlit as st 
from datetime import datetime, timedelta
from PIL import Image
import plotly.graph_objects as go
import matplotlib.pyplot as plt

def app(): 

    #sidebar for date selection 
    start_date = st.sidebar.date_input("start_date")
    end_date = st.sidebar.date_input("end_date")

    if start_date <= end_date : 
        st.sidebar.success(f"start date : {start_date}\n\nend date : {end_date}")
    else : 
        st.sidebar.error("You can't have the start date greater than the end date")

    date_range_selector = toPyDate(pd.date_range(start_date, end_date))

    #preprocessing
    df_workout = pd.read_csv(r"D:\Users\lucas\Bureau\project\health_app\right_files\workout.csv")
    df_workout["@creationDate"] = pd.to_datetime(df_workout["@creationDate"])
    df_workout["@startDate"] = pd.to_datetime(df_workout["@startDate"])
    df_workout["@endDate"] = pd.to_datetime(df_workout["@endDate"])
    df_workout["Date"] = toPyDate(pd.to_datetime(df_workout["@creationDate"]).to_list())

    df_record = pd.read_csv(r"D:\Users\lucas\Bureau\project\health_app\right_files\record.csv")
    heart_rate = df_record["@type"] == "HKQuantityTypeIdentifierHeartRate"
    df_heart_rate = df_record[heart_rate]
    df_heart_rate["Date"] = toPyDate(pd.to_datetime(df_heart_rate["@creationDate"]).to_list())
    df_heart_rate["@creationDate"] = pd.to_datetime(df_heart_rate["@creationDate"])
    df_heart_rate["@startDate"] = pd.to_datetime(df_heart_rate["@startDate"])
    df_heart_rate["@endDate"] = pd.to_datetime(df_heart_rate["@endDate"])

    #global burned cal 
    df_workout_global = df_workout.groupby(["Date"]).sum().reset_index()
    filter_burned = df_workout_global["Date"].isin(date_range_selector)
    burned = df_workout_global[filter_burned]["@totalEnergyBurned"].sum()

    #total duration 
    duration = df_workout_global[filter_burned]["@duration"].sum()

    #min and max heart rate 
    filter_heart = df_heart_rate["Date"].isin(date_range_selector)
    min_hrate = df_heart_rate[filter_heart]["@value"].min()
    max_hrate = df_heart_rate[filter_heart]["@value"].max()

    #avg cal/number of time exercice 
    filter_avg= df_workout["Date"].isin(date_range_selector)
    nb_workout = len(df_workout[filter_avg])
    avg_burned = burned/nb_workout
    avg_time = duration/nb_workout


    total_burned, time_exercice, max_heart_rate, min_heart_rate = st.columns(4)
    mean_burned, mean_time_exercice, most_moment,none = st.columns(4)

    total_burned.metric("sum of burned calorie", round(burned,2))

    if duration > 60 : 
        durations = duration/60
        time_exercice.metric("total time exersiced (h)", round(durations,2))
    else : 
        time_exercice.metric("total time exersiced (min)", round(duration,2))

    max_heart_rate.metric("Max heart rate",max_hrate)
    min_heart_rate.metric("Min heart rate",min_hrate)
    mean_burned.metric("Avg cal burned",round(avg_burned,2))
    mean_time_exercice.metric("Avg time exercice (min)",round(avg_time,2))

    #display text info
    workout_info = df_workout[df_workout["Date"].isin(date_range_selector)]
    workout_info.groupby("@workoutActivityType").count().reset_index()
    workout_group = workout_info.groupby("@workoutActivityType").count().reset_index().sort_values("@workoutActivityType")
    Types = workout_group["@workoutActivityType"]
    quantities = workout_group["@duration"]

    #avg 
    workout_avg = df_workout[df_workout["Date"].isin(date_range_selector)]
    workout_avg = workout_avg.groupby("@workoutActivityType").mean().reset_index().sort_values("@workoutActivityType")
    time_by_activity = workout_avg["@duration"]

    st.header("General workout information")

    text = f'''From **{start_date}** to **{end_date}** you performed a total of **{nb_workout}**.
            The type of activity you did was : '''

    st.markdown(text)

    for Type, quantity, time in zip(Types, quantities, time_by_activity) : 
        activity = Type.find("Type")
        st.markdown(f"""- **{Type[activity+4:]}** for a total of **{round(quantity)}** times and an average duration of **{round(time)}** min \n""", )


    #second part : detail of workout 
    st.header("Comparison of two workouts")

    st.markdown('when you comparing 2 workout you will have information about : \n '
                '- how low it last and what is its contribution in a day (fix value **60 min**) \n'
                '- how much calories you burned and its contribution in a day (fix value **700 cal**)')

    workout_filter_date = df_workout["Date"].isin(date_range_selector)
    df_workout["workout"] = df_workout["@workoutActivityType"] + " " + df_workout["@creationDate"].astype(str)

    #select max 2 to compare 
    workout_detail = st.multiselect(
        'what are the workout you would like to be detailed ?',
        df_workout[workout_filter_date]["workout"],df_workout[workout_filter_date]["workout"].head(2))

    df_workout_filter = df_workout[workout_filter_date]

    if len(workout_detail) == 2  : 
        ref = df_workout[df_workout["workout"].isin(workout_detail)]

        left_workout, right_workout = st.columns(2)
        left_duration, left_calories, right_duration, right_calories = st.columns(4)
        left_chart, right_chart = st.columns(2)
        left_heart, right_heart = st.columns(2)

        #left_workout 
        format_subheader = workout_detail[0].find("Type")
        subheader = workout_detail[0][format_subheader+4 :]
        left_workout.subheader(subheader)
        left_duration.metric("Workout duration (min)", round(ref["@duration"].to_list()[0]))
        left_calories.metric("Calorie Burned (Kcal)", round(ref["@totalEnergyBurned"].to_list()[0]))
        
        #radial bar left 
        calorie = ref["@totalEnergyBurned"].to_list()[0]
        duration = ref["@duration"].to_list()[0]
        percent = [calorie,duration]
        categories = ["calorie burned","workout time"]
        chart_1 = draw_radial_bar(categories,percent)
        left_chart.pyplot(chart_1)

        #heart rate left chart 
        start_hr_left, start_hr_right = ref["@startDate"].to_list()
        end_hr_left, end_hr_right = ref["@endDate"].to_list()

        filter_left_hr = (df_heart_rate["@startDate"] >= start_hr_left) & (df_heart_rate["@endDate"] <= end_hr_left + timedelta(minutes=3))
        left_hr = df_heart_rate[filter_left_hr]
        recovery_left = df_heart_rate[(df_heart_rate["@startDate"] >= end_hr_left) & 
                        (df_heart_rate["@endDate"] <= end_hr_left + timedelta(minutes=3))]
        
        left_scatter = draw_scatter_plot(left_hr["@endDate"],left_hr["@value"],
                                        recovery_left["@endDate"],recovery_left["@value"])
        
        left_heart.plotly_chart(left_scatter)
        

        filter_right_hr = (df_heart_rate["@startDate"] >= start_hr_right) & (df_heart_rate["@endDate"] <= end_hr_right + timedelta(minutes=3))
        right_hr = df_heart_rate[filter_right_hr]
        recovery_right = df_heart_rate[(df_heart_rate["@startDate"] >= end_hr_right) & 
                        (df_heart_rate["@endDate"] <= end_hr_right + timedelta(minutes=3))]

        right_scatter = draw_scatter_plot(right_hr["@endDate"],right_hr["@value"],
                                        recovery_right["@endDate"],recovery_right["@value"])
        
        right_heart.plotly_chart(right_scatter)
        

        
        #right_workout
        format_subheader = workout_detail[1].find("Type")
        subheader = workout_detail[1][format_subheader+4 :]
        right_workout.subheader(subheader)
        right_duration.metric("Workout duration (min)", round(ref["@duration"].to_list()[1]))
        right_calories.metric("Calorie Burned (Kcal)", round(ref["@totalEnergyBurned"].to_list()[1]))

        #radial bar right
        calorie_1 = ref["@totalEnergyBurned"].to_list()[1]
        duration_1 = ref["@duration"].to_list()[1]
        percent_1 = [calorie_1,duration_1]
        chart_2 = draw_radial_bar(categories,percent_1)
        right_chart.pyplot(chart_2,size=15)

    else : 
        st.write("select 2 elements")

