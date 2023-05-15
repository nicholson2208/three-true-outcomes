from bokeh.plotting import figure, save, output_file, show
from bokeh.models import (ColumnDataSource, DataTable, DateFormatter, 
                          TableColumn, HoverTool, PolyAnnotation, CategoricalColorMapper,
                         Circle)
from bokeh.transform import factor_cmap
from bokeh.layouts import row, column
from bokeh.io import output_notebook
from bokeh.embed import file_html
from bokeh.resources import CDN
import pandas as pd
from datetime import date, timedelta


run_dt = str(date.today() + timedelta(days=-1))
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
        TableColumn(field="plate_x", title="Plate X"),
        TableColumn(field="plate_z", title="Plate Z"),
    ]

data_table = DataTable(source=source, 
                       columns=columns, 
                       width=800, 
                       height=280)

# create a new plot with a title and axis labels
group = df.groupby("events")

p = figure(title="Count of All Events for {}".format(run_dt),
           x_range=group,
           x_axis_label='Outcomes',
           y_axis_label='Frequency',
           tools="",
           width=400, 
           height=400)

# add a line renderer with legend and line thickness to the plot

outcome_counts = p.vbar(x="events", 
                        bottom=0, 
                        top="strikes_count",
                        source=group,
                        width=0.8)

tooltips_bar = [
    ("Freqency ", "@events: @strikes_count"),
]

outcome_hover = HoverTool(renderers=[outcome_counts], tooltips=tooltips_bar)
p.add_tools(outcome_hover)


# this is for the colors in the strike zone plot
factors = df["events"].unique()

# make a strike zone figure

sz = figure(width=400,
            height=400, 
            tools="box_select,reset", 
            active_drag="box_select")

# I think this plot from the center
sz.rect(0, 2.5, 2*0.71, 2,
        fill_alpha = 0,
        line_width = 3,
        line_color = "gray"
       )

home_plate_coords = [[-0.71, 0], [-0.85, -0.5], [0, -1], [0.85, -0.5], [0.71, 0]]

home_plate = PolyAnnotation(
    fill_color="lightgray",
    fill_alpha=0.4,
    line_color="darkgray",
    line_width=3,
    xs=list(map(lambda coord: coord[0], home_plate_coords)),
    ys=list(map(lambda coord: coord[1], home_plate_coords)),
)

sz.add_layout(home_plate)

pitches = sz.circle(x="plate_x",
                    y="plate_z", 
                    color=factor_cmap('events',
                                      palette="Spectral{}".format(len(factors)+1),
                                      factors=factors),
                    size=25,
                    alpha=0.35,
                    source=source)

# change the styling for selected v not
selected_circle = Circle(fill_alpha=0.6,
                         line_color = None,
                         fill_color=factor_cmap('events',
                                                palette="Spectral4",
                                                factors=factors))

nonselected_circle = Circle(fill_alpha=0.1,
                         line_color = None,
                         fill_color=factor_cmap('events',
                                                palette="Spectral4",
                                                factors=factors))
pitches.selection_glyph = selected_circle
pitches.nonselection_glyph = nonselected_circle

tooltips = [
    ("Batter", "@batter"),
    ("Pitch Type", "@pitch_type"),
    ("Pitch Speed", "@release_speed"),
    ("Outcome", "@events"),
    ("Exit Velo", "@launch_speed"),
    ("Plate X", "@plate_x"),
    ("Plate Z", "@plate_z")
]

pitches_hover_tool = HoverTool(renderers=[pitches], tooltips=tooltips)

sz.add_tools(pitches_hover_tool)


sz.axis.visible = False
sz.grid.visible = False


with open("index_template.html") as template:
    template = template.read()
    
out_html = file_html(column(data_table, row(p, sz)),
                     CDN,
                     template=template,
                     template_variables={"run_dt" : run_dt},
                     title="Three True Outcomes for {}".format(run_dt))

with open("index.html", "w") as output:
    output.write(out_html)

