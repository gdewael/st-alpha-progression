import pandas as pd
from datetime import datetime
import numpy as np
import streamlit as st
import plotly.express as px

st.set_page_config(page_title="Gym progress visualizer", page_icon="🏋️")

st.title("Gym progress visualizer ")
st.write("##### (Based on export data from Alpha Progression)")
st.write("If you encounter issues/errors with this script, you can open an issue [on GitHub](https://github.com/gdewael/st-alpha-progression/issues) (or get in touch with me otherwise).")

def RM1(reps, weight):
    return weight / (1.0278 - 0.0278*reps)

def RM10(reps, weight):
    return (1.0278 - 0.0278*10)*RM1(reps, weight)

def RM10_to_RM1(RM10):
    return RM10/(1.0278 - 0.0278*10)

def RM1_to_RMx(RM1, r):
    return RM1 * (1.0278 - 0.0278 * r)

uploaded_file = st.file_uploader("Input Alpha Progression workouts file")

if uploaded_file is not None:
    data = pd.read_csv(uploaded_file, delimiter=";", header=None)
    #data = pd.read_csv("workouts.csv", delimiter=";", header=None)

    is_start_workout_row = []
    for i in range(len(data)):
        try:
            datetime.strptime(data.iloc[i,1][:-3], "%Y-%m-%d %H:%M")
            is_start_workout_row.append(True)
        except:
            is_start_workout_row.append(False)


    is_start_workout_row = np.where(is_start_workout_row)[0]
    is_start_workout_row = np.append(is_start_workout_row, len(data))

    exercises = {}

    for i in range(len(is_start_workout_row)-1):
        workout = data.iloc[is_start_workout_row[i]+1:is_start_workout_row[i+1]]

        workout_date = datetime.strptime(
            data.iloc[is_start_workout_row[i], 1][:-3],
            "%Y-%m-%d %H:%M"
            ).strftime("%Y-%m-%d")
        
        for row in range(len(workout)):
            if pd.isnull(workout.iloc[row, 2]):
                name = "·".join(workout.iloc[row,0].split(".")[1].split("·")[:2]).strip()
            elif (workout.iloc[row, 1] != "KG") and (not name.startswith("Running on Treadmill")):
                if name in exercises:
                    exercises[name].append((workout_date, float(workout.iloc[row, 1]), int(workout.iloc[row, 2])))
                else:
                    exercises[name] = [(workout_date, float(workout.iloc[row, 1]), int(workout.iloc[row, 2]))]


    x = {k : len(v) for k, v in exercises.items()}
    exercise_freq = pd.DataFrame(list(sorted(x.items(), key=lambda item: item[1], reverse=True)))

    def format_func(i):
        return exercise_freq.iloc[i][0] + " (Total sets: " + str(exercise_freq.iloc[i][1]) + ")"


    exercise_to_plot = st.selectbox("Select exercise to plot", options = np.arange(len(exercise_freq)), format_func = format_func)
    
    options = {
        "Smoothed Average" : ("lowess", dict(frac=0.8)),
        "Follow max" : ("expanding", dict(function="max")),
    }

    trendline = st.radio(
        "Select trendline type",
        ["Smoothed Average", "Follow max"]
    )

    exercise_to_plot = exercise_freq.iloc[exercise_to_plot, 0]

    data_exercise = pd.DataFrame(exercises[exercise_to_plot], columns = ["Date", "Weight", "Reps"])
    data_exercise["Date"] = pd.to_datetime(data_exercise["Date"])
    data_exercise["Estimated 10RM"] = RM10(data_exercise["Reps"], data_exercise["Weight"])
    data_exercise["1RM"] = RM1(data_exercise["Reps"], data_exercise["Weight"])

    


    fig = px.scatter(
        data_exercise,
        x="Date",
        y="Estimated 10RM",
        trendline=options[trendline][0],
        trendline_options=options[trendline][1],
        color_discrete_sequence=["lime"],
        opacity = 0.5,
        hover_data=["Date", "Weight", "Reps", "Estimated 10RM"],
    )
    
    est_rm10 = fig.data[1].y[-1]
    est_rm1 = RM10_to_RM1(est_rm10)

    title_ = "Est. 10RM: %.2f / Est. 1RM: %.2f" % (est_rm10, est_rm1)
    fig.update_layout(
        title=dict(
            text=title_
            )
        )
    st.plotly_chart(fig, use_container_width=False)

    st.write("Rep to weight table:")
    st.dataframe(
        pd.DataFrame([[RM1_to_RMx(est_rm1, r) for r in range(1, 21)]], columns = np.arange(1, 21)),
        hide_index = True
    )