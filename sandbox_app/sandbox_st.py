import streamlit as st
import pandas as pd
import altair as alt

st.write("Sandbox")

# Define rectangle coordinates
rect_data = pd.DataFrame([{
    "x_start": 0, "x_end": 10,
    "y_start": 0, "y_end": 10
}])

# Draw rectangle
chart = (
    alt.Chart(rect_data)
    .mark_rect(fill=None, stroke="black", strokeWidth=2)
    .encode(
        x=alt.X("x_start:Q", title="Axe X", scale=alt.Scale(domain=[-2, 12])),
        x2="x_end",
        y=alt.Y("y_start:Q", title="Axe Y", scale=alt.Scale(domain=[-2, 12])),
        y2="y_end"
    )
    .properties(
        width=400,
        height=400,
        title="Rectangle de x=0,y=10 à x=10,y=0"
    )
)

st.altair_chart(chart, use_container_width=True)
