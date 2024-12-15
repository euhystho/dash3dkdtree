from tree import KDTree
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, State, ClientsideFunction
from flask_caching import Cache

def make_tree():
    tree = KDTree()
    tree.add(50,50,50)
    tree.add(25,25,25)
    tree.add(25,50,20)
    tree.add(25,10,10)
    tree.add(25,10,5)
    tree.add(25,10,20)
    tree.add(75,75,75)
    tree.add(75,10,5)
    tree.add(75,100,30)
    tree.add(75,10,20)
    tree.add(75,10,50)
    tree.add(75,100,70)
    tree.add(75,100,90)
    return tree

if __name__ == "__main__":
#TODO: Maybe not have it pre-determined for the user, possibly add the ability to put stuff, but it could also just make it hard...
    tree = make_tree()

    # Initialize the Dash app with the Bootstrap Theme :O
    app = Dash(external_stylesheets=[dbc.themes.COSMO])
    app.title = '3D KD Tree Demo'

#Cache the KD Tree into memory for the spherical calculations :)
    cache = Cache(app.server, config = { 
        'CACHE_TYPE': 'simple'
    })
    cache.set('kdtree', tree)

# Figures for plotly
    fig = go.Figure()

    fig = make_subplots(
        rows = 1,
        cols = 2,
        column_widths= [0.5,0.5],
        specs = [[{"type": "scatter"}, {"type": "surface"}]],
        subplot_titles= ("2D Tree Representation of the KD Tree", "KD Tree")
    )

# Get the Figure from the Tree
    fig = tree.draw(fig)

# Make it Pretty through removing legend for traces on the 2D KD Representation and reducing margins so you see more of the graph 
    fig.update_layout(showlegend = False,
                      margin = dict(l = 40, r = 20, t = 20, b = 20)
    )
    fig.update_xaxes(showticklabels = False, row = 1, col = 1)
    fig.update_yaxes(showticklabels = False, row = 1, col = 1)
    
# All of the dbc.Cards are just the HTML Content using Bootstrap
    intro_content = dbc.Card(
        dbc.CardBody(
            [
                html.H4("Background: ", className = "card-text"),
                html.P("If you might not already know what KD Trees are, they are simply K-Dimensional Binary Search Trees, in this app it represents the 3rd Dimension or a 3-Dimensional (3D) Tree.", className = "card-text"),
                html.P("Binary Search Trees (BSTs) start with a root node (the highest point of the left graph), and for every left side of the root, the value is less than the root, and for the right side, the value is greater than the root. Elevating this concept to a KD Tree, consider the relationship of the root's left and right child of the x-coordinate, then the y-coordinate, then the z-coordinate, and after that continue wrapping around x, y, and z.",className = "card-text"),
                html.P("To see this for yourself, hover over the points in the tree on the bottom left!", className="card-text"),
                html.P("On the bottom right is a 3D plot of the 3D KD Tree, each of the points have a plane attached to them with the space on the sides of the plane indicating values that are less or greater than them in their respective coordinate level on the tree.", className="card-text"),
                dbc.Table([
                    html.Thead(
                        html.Tr([html.Th("Legend for the Coordinate Plane Colors")])
                    ),
                    html.Tbody([
                        html.Tr([
                            html.Td("X", className = "bg-danger", title = "Uses the Reds colorscale"),
                        ]),
                        html.Tr([
                            html.Td("Y", className = "bg-success", title = "Uses the Greens colorscale"),
                        ]),
                        html.Tr([
                            html.Td("Z", className = "bg-primary", title = "Uses the Teal colorscale"),
                        ])
                    ])
                ], bordered=True, hover = True, responsive= True, striped=True),
                dcc.Graph(id ='kd-tree-intro',
                          figure = fig)
            ]
        ),
        className = "mt-3"
    )
    sphere_content = dbc.Card(
    dbc.CardBody(
        [
            html.H4("Input Coordinates and Radius", className="card-title"),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Input(
                            id="a_val",
                            type="number",
                            min=0,
                            max=100,
                            placeholder="Enter x-coordinate",
                            style={"margin-bottom": "10px"},
                            value=''
                        ),
                        width=3
                    ),
                    dbc.Col(
                        dcc.Input(
                            id="b_val",
                            type="number",
                            min=0,
                            max=100,
                            placeholder="Enter y-coordinate",
                            style={"margin-bottom": "10px"},
                            value=''
                        ),
                        width=3
                    ),
                    dbc.Col(
                        dcc.Input(
                            id="c_val",
                            type="number",
                            min=0,
                            max=100,
                            placeholder="Enter z-coordinate",
                            style={"margin-bottom": "10px"},
                            value=''
                        ),
                        width=3
                    ),
                    dbc.Col(
                        dcc.Input(
                            id="r_val",
                            type="number",
                            placeholder="Enter radius",
                            style={"margin-bottom": "10px"},
                            value=''
                        ),
                        width=3
                    ),
                ],
                className="mb-3"
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Button(
                        "Compute Neighbors!",
                        id="traverse-button",
                        className="me-1",
                        size="sm",
                        n_clicks=0
                    ),
                    width="auto"
                ),
                justify="center"
            ),
            html.Hr(),
            html.Div(id="sphere_neighbors_out"),
            html.Hr(),
            html.H4("Color Guide", className="card-title"),
            html.P("Below is a brief overview of the node traversal colors and what they mean when traversing the tree:"),
            dbc.Table(
                [
                    html.Thead(
                        html.Tr([html.Th("Node Color"), html.Th("Meaning")])
                    ),
                    html.Tbody(
                        [
                            html.Tr([
                                html.Td("Orange", className="bg-warning text-white"),
                                html.Td("The node is currently being visited"),
                            ]),
                            html.Tr([
                                html.Td("Green", className="bg-success text-white"),
                                html.Td("The node is a neighbor within the sphere")
                            ]),
                            html.Tr([
                                html.Td("Red", className="bg-danger text-white"),
                                html.Td("The node is not a neighbor within the sphere")
                            ]),
                            html.Tr([
                                html.Td("Black", className="bg-dark text-white"),
                                html.Td("The node has not been visited yet")
                            ])
                        ]
                    )
                ],
                bordered=True,
                responsive=True,
                striped=True
            ),
            dcc.Graph(id= 'kd-tree-sphere',
                      figure = fig)
        ]
    ),
    className="mt-3"
)
    sphere_content = dbc.Card(
    dbc.CardBody(
        [
            html.H4("Input Coordinates and Radius", className="card-title"),
            dbc.Row(
                [
                    dbc.Col(
                        dcc.Input(
                            id="a_val",
                            type="number",
                            min=0,
                            max=100,
                            placeholder="Enter x-coordinate",
                            style={"margin-bottom": "10px"},
                            value=''
                        ),
                        width=3
                    ),
                    dbc.Col(
                        dcc.Input(
                            id="b_val",
                            type="number",
                            min=0,
                            max=100,
                            placeholder="Enter y-coordinate",
                            style={"margin-bottom": "10px"},
                            value=''
                        ),
                        width=3
                    ),
                    dbc.Col(
                        dcc.Input(
                            id="c_val",
                            type="number",
                            min=0,
                            max=100,
                            placeholder="Enter z-coordinate",
                            style={"margin-bottom": "10px"},
                            value=''
                        ),
                        width=3
                    ),
                    dbc.Col(
                        dcc.Input(
                            id="r_val",
                            type="number",
                            placeholder="Enter radius",
                            style={"margin-bottom": "10px"},
                            value=''
                        ),
                        width=3
                    ),
                ],
                className="mb-3"
            ),
            dbc.Row(
                dbc.Col(
                    dbc.Button(
                        "Compute Neighbors!",
                        id="traverse-button",
                        className="me-1",
                        size="sm",
                        n_clicks=0
                    ),
                    width="auto"
                ),
                justify="center"
            ),
            html.Hr(),
            html.Div(id="sphere_neighbors_out"),
            html.Hr(),
            html.H4("Color Guide", className="card-title"),
            html.P("Below is a brief overview of the node traversal colors and what they mean when traversing the tree:"),
            dbc.Table(
                [
                    html.Thead(
                        html.Tr([html.Th("Node Color"), html.Th("Meaning")])
                    ),
                    html.Tbody(
                        [
                            html.Tr([
                                html.Td("Orange", className="bg-warning text-white"),
                                html.Td("The node is currently being visited"),
                            ]),
                            html.Tr([
                                html.Td("Green", className="bg-success text-white"),
                                html.Td("The node is a neighbor within the sphere")
                            ]),
                            html.Tr([
                                html.Td("Red", className="bg-danger text-white"),
                                html.Td("The node is not a neighbor within the sphere")
                            ]),
                            html.Tr([
                                html.Td("Black", className="bg-dark text-white"),
                                html.Td("The node has not been visited yet")
                            ])
                        ]
                    )
                ],
                bordered=True,
                responsive=True,
                striped=True
            ),
            dcc.Graph(id= 'kd-tree-sphere',
                      figure = fig)
        ]
    ),
    className="mt-3"
    )
    # Define the dash app layout
    app.layout = html.Div([
        html.H1(dcc.Markdown('3D KD Tree by [Eugene Thompson](https://github.com/euhystho)'), className = 'custom-link', style = {'textAlign': 'center'}),
        dbc.Tabs(
            [
                dbc.Tab(intro_content, label = "Introduction", tab_id = "intro"),
                dbc.Tab(sphere_content, label = "Sphere Neighbor Traversal", tab_id = "sphere"),
            ],
            id = "tabs",
            active_tab = "intro"
        ),
    ])

# Sad Javascript Clientside Callback ;-;
    app.clientside_callback(
        ClientsideFunction(
            namespace='clientside',
            function_name='findSphereNeighbors'
        ),
        Output("sphere_neighbors_out", "children"),
        Output("kd-tree-sphere", "figure"),
        Input("kd-tree-sphere", "figure"),
        Input("traverse-button", "n_clicks"),
        State("a_val", "value"),
        State("b_val", "value"),
        State("c_val", "value"),
        State("r_val", "value"),
    )
# Run the app :D
    app.run_server(debug = False)

