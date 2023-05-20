from bokeh.plotting import figure, save, output_file, show
from bokeh.models import (ColumnDataSource, DataTable, DateFormatter, 
                          TableColumn, HoverTool, PolyAnnotation, CategoricalColorMapper,
                         Circle, CustomJS, MultiChoice, IndexFilter, CDSView)
from bokeh.transform import factor_cmap
from bokeh.palettes import Spectral11
from bokeh.layouts import row, column
from bokeh.io import output_notebook
from bokeh.embed import file_html
from bokeh.resources import CDN
import pandas as pd
from datetime import date, timedelta

from pybaseball import playerid_reverse_lookup


run_dt = str(date.today() + timedelta(days=-1))
df = pd.read_csv("data/tto_events.csv")

# turn the player id of batters into a readable name
batter_names_df = playerid_reverse_lookup(df.batter, key_type='mlbam')

batter_names_df.loc[:, "batter_name"] = (batter_names_df.name_first + " " + batter_names_df.name_last)
batter_names_df.loc[:, "batter_name"] = batter_names_df.loc[:, "batter_name"].apply(str.title)

df = df.merge(batter_names_df[["key_mlbam", "batter_name"]],
              left_on='batter',
              right_on='key_mlbam',
              how="left")

plot_data = df["events"].value_counts()
outcomes = list(plot_data.index)
# print(plot_data.columns)

source = ColumnDataSource(df)

plot_filter = IndexFilter(list(range(df.shape[0])))
plot_view = CDSView(filter=plot_filter)

columns = [
        TableColumn(field="batter_name", title="Batter"),
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
                       height=280,
                       view=plot_view
                      )


# make a multi_choice thing with a callback to filter the data

factors = list(df["events"].unique())

multi_choice = MultiChoice(value=["home_run", "strikeout", "walk"], options=factors, width=800, height=50)


# so I think the problem here is that I want this to count! but it doesn't have numbers to count

grouped_data = df.groupby(by = ["events", "pitch_type"]).size().unstack(fill_value=0)
categories = grouped_data.index.tolist()
subcategories = grouped_data.columns.tolist()

source_grouped = ColumnDataSource(data=grouped_data)

pitch_colors = [Spectral11[ii%11] for ii in range(20)]

p = figure(x_range=categories, height=400, width=400, title="", tools="")

bars = p.vbar_stack(subcategories,
                    x='events',
                    width=0.9,
                    line_color=pitch_colors[:len(subcategories)],
                    fill_color=pitch_colors[:len(subcategories)],
                    legend_label=subcategories,
                    source=source_grouped)#, view=plot_view)

# p.legend.orientation = "horizontal"
# p.legend.location = "top_center"
p.legend.visible = False

# Add tooltips
p_tooltips = [
    ("Outcome", "@events"),
    ("Pitch Type", "$name: @$name")
]

p.add_tools(HoverTool(renderers=bars, tooltips=p_tooltips))

# make a strike zone figure

sz = figure(width=400,
            height=400, 
            tools="box_select,reset,zoom_in,zoom_out", 
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
                    size=20,
                    alpha=0.35,
                    source=source,
                    view=plot_view
                   )

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
    ("Batter", "@batter_name"),
    ("Pitch Type", "@pitch_type"),
    ("Pitch Speed", "@release_speed{0.1f}"),
    ("Outcome", "@events"),
    ("Exit Velo", "@launch_speed{0.1f}"),
    ("Plate X", "@plate_x"),
    ("Plate Z", "@plate_z")
]

pitches_hover_tool = HoverTool(renderers=[pitches], tooltips=tooltips)

sz.add_tools(pitches_hover_tool)


sz.axis.visible = False
sz.grid.visible = False

multi_choice.js_on_change("value", CustomJS(args=dict(source=source, plot_filter=plot_filter, columns=columns), code="""    
    let sData = source.data

    // filter if the event it one of the choices
    const isSelectedOutcome = (element) => this.value.includes(element);
    
    // let selectedIndices = s_data.events.findIndex(isSelectedOutcome)
    let selectedIndices = sData.events.map((x, index) => { if(isSelectedOutcome(x)) return index}).filter(item => item !== undefined)
    
    plot_filter.indices = selectedIndices
    source.change.emit()
"""))


with open("index_template.html") as template:
    template = template.read()
    
out_html = file_html(column(multi_choice, data_table, row(p, sz)),
                     CDN,
                     template=template,
                     template_variables={"run_dt" : run_dt},
                     title="Three True Outcomes for {}".format(run_dt))

with open("index.html", "w") as output:
    output.write(out_html)

