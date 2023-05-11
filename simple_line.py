from bokeh.plotting import figure, show, output_file
from bokeh.models import ColumnDataSource, DataTable, DateFormatter, TableColumn
from bokeh.layouts import row
import pandas as pd

# prepare some data
x = [1, 2, 3, 4, 5]
y = [6, 7, 2, 4, 5]


df = pd.read_csv("data/tto_events.csv")

plot_data = df["events"].value_counts()
outcomes = list(plot_data.index)
# print(plot_data.columns)

source = ColumnDataSource(df)

columns = [
        TableColumn(field="batter", title="Batter"),
        TableColumn(field="pitch_type", title="Pitch Type"),
        TableColumn(field="release_speed", title="Pitch Speed"),
        TableColumn(field="events", title="Outcome"),
        TableColumn(field="launch_speed", title="Exit Velo"),
    ]
data_table = DataTable(source=source, 
                       columns=columns, 
                       width=400, 
                       height=280)

# create a new plot with a title and axis labels
p = figure(title="Count of Three True Outcome Events",
            x_range=outcomes,
            x_axis_label='outcomes',
            y_axis_label='frequency',
            tools="hover",
            width=400, 
            height=280)

# add a line renderer with legend and line thickness to the plot

p.vbar(x=plot_data.index, bottom=0, top=plot_data.values,
        width=0.8)

output_file('index.html')

save(row(p, data_table))
