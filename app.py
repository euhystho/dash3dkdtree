# from flask import jsonify, request
from tree import KDTree
import numpy as np
import plotly.graph_objects as go
import dash_bootstrap_components as dbc
from plotly.subplots import make_subplots
from dash import Dash, dcc, html, Input, Output, State, callback
from flask_caching import Cache


@callback(
    Output("sphere_neighbors_out", "children"),
    Output("kd-tree-sphere", "figure"),
    Input("kd-tree-sphere", "figure"),
    Input("traverse-button", "n_clicks"),
    State("a_val", "value"),
    State("b_val", "value"),
    State("c_val", "value"),
    State("r_val", "value"),
    
)
def find_sphere_neighbors(fig, clicks, a, b, c, r):
    """
    Finds the Sphere's neighbors that are within the sphere by checking each pole and the north, south, east, west of the equator

    Args:
        a (float): x-coordinate of the center of the sphere
        b (float): y-coordinate of the center of the sphere
        c (float): z-coordinate of the center of the sphere
        r (float): radius of the sphere
        clicks (int): represents the number of clicks the button has received :)

    Returns:
        str: a pretty print version of the neighbors of the sphere
    """
# Since this function is in a callback in dash, the KD Tree is in the flask cache for quick access
    tree = cache.get('kdtree')
# Empty until Found :)
    found = False
    results = []
    ret = ""
# Checks if the user has started the traverse or not:
    if clicks > 0 and (a and b and c and r):
    #Assume there's none until proven otherwise
        ret = "There are no neighbors in this sphere!"
        results, found, coordinates, inorder_neighbors = tree.find_sphere_neighbors(a,b,c,r)

    # Time to Animate Traversal! YAYYYYYYYYYYY
        frames = traversal_animation(coordinates,inorder_neighbors)

    #Plots the sphere and hide the barriers from the graph
        fig = plot_sphere(a, b, c, r)

        fig.frames = frames
        fig.update_layout( 
            scene=dict( 
                xaxis=dict(showspikes=False), 
                yaxis=dict(showspikes=False), 
                zaxis=dict(showspikes=False), 
            ), 
            updatemenus=[ { 
                "buttons": [ { "args": [None, {"frame": {"duration": 1250, "redraw": True}, "fromcurrent": True}], "label": "Traverse Tree", "method": "animate" },
            {"args": [[None], {"frame": {"duration": 0, "redraw": True}, "mode": "immediate", "transition": {"duration": 0}}], "label": "Pause Traversal", "method": "animate" 
             }],
        "direction": "left", "pad": {"r": 10, "t": 20},"showactive": False, "type": "buttons", "x": 0.1, "xanchor": "right", "y": 0, "yanchor": "top" } ] )
    # Create a string so that the results look nicer
        neighbs = ", ".join([str(result) for result in results])

#Printing Stuff:
    found_status = "in the tree" if found else "not in the tree"
# Printing Logic
    if len(results) != 0:
        ret = f" The coordinate {(a,b,c)} is {found_status} and its neighbors' coordinates are: {neighbs}"
        alert = dbc.Alert(ret, color = "success")
    elif (a and b and c and r):
        alert = dbc.Alert(ret, color = "info")
    else:
        alert = dbc.Alert("Please enter all coordinates and the radius...", color = "warning")

    return alert, fig

def plot_sphere(a, b, c, r):
# Remove the barriers, and create the sphere :)
    fig.update_traces(visible = False, selector= dict(type = 'surface'))
    sphere = create_sphere(a,b,c,r)
    fig.add_trace(sphere)
    return fig

def create_sphere(a, b, c, r):

# Points in the Meshgrid
    n = 50

# Using the Formula of a sphere below:
    theta = np.linspace(0, np.pi, n)
    phi = np.linspace(0, 2 * np.pi, n)
    theta, phi = np.meshgrid(theta, phi)

    x = r * np.sin(theta) * np.cos(phi) + a
    y = r * np.sin(theta) * np.sin(phi) + b
    z = r * np.cos(theta) + c
#Put the arrays into a surface to display it in plotly :)
    sphere = go.Surface(x = x,
                        y = y,
                        z = z,
                        name = "sphere",
                        colorscale='Peach',
                        showscale = False,

                    #PLEASE DO NOT TURN THIS TO TRUE D:
                    #Turning off contours is good for your sanity... (it removes lines that contour around the sphere,
                    #If you keep dragging the sphere around with these turned on, it gives you tons of lines around the sphere
                        contours={"x.highlight": False, 
                                  "y.highlight": False, 
                                  "z.highlight": False})
    return sphere

def traversal_animation(coors,neighbs):
    scatter_list = [trace.to_plotly_json() for trace in fig.data if isinstance(trace, go.Scatter)]
    surface_list = [trace.to_plotly_json() for trace in fig.data if isinstance(trace, go.Surface)]

    checking_node_color = 'orange'
    neighboring_node_color = 'green'
    stranger_node_color = 'red'

    # Create a list of frames for the animation
    frames = []

    # Create a dictionary to map the coordinates with the traces
    trace_dict = {}
    for trace in scatter_list:
        if trace['hoverinfo'] == 'text':
            coordinate = (trace['x'][0], trace['y'][0])
            trace_dict[coordinate] = trace

    seen_neighbors = set()

    for i in range(len(coors)):
        updated_data = scatter_list.copy()
        # Calculate ax based on the position in the tree
        if i == 0:
            ax, ay = 0, 75  # Root
        elif i % 2 == 0:
            ax, ay = -50, -40  # Left
        else:
            ax, ay = 50, -40  # Right
        
        tree_coor = coors[i][0]
        graph_coor = coors[i][1]

        plane = None
        for surface in surface_list:
            if surface['name'] == str(graph_coor):
                surface['colorscale'] = "gray"
                plane = surface

        updated_data.append(plane)

        # Update the color of the corresponding trace
        if tree_coor in trace_dict:
            trace_dict[tree_coor]['marker']['color'] = checking_node_color

        if neighbs[i]:
            coord = neighbs[i]
            if coord in trace_dict:
                trace_dict[coord]['marker']['color'] = neighboring_node_color
                seen_neighbors.add(coord)

        for coord, trace in trace_dict.items():
            if coord != tree_coor and trace['marker']['color'] == checking_node_color:
                trace_dict[coord]['marker']['color'] = stranger_node_color

        # Create a frame with the updated trace and the arrow annotation
        frame = go.Frame(
            data=updated_data,
            layout=go.Layout(
                annotations=[
                    go.layout.Annotation(
                        x=tree_coor[0],
                        y=tree_coor[1],
                        ax=ax,
                        ay=ay,
                        xref="x",
                        yref="y",
                        text="Current Node",
                        showarrow=True,
                        font=dict(size=16, color="#ff0000"),
                        arrowhead=2,
                        arrowsize=1,
                        arrowwidth=3,
                        arrowcolor="#ff0000",
                        opacity=0.8
                    )
                ]
            ),
            name=f'frame{i}'
        )
        frames.append(frame)

    # Check Final Value:
    if tree_coor == neighbs[-1]:
        trace_dict[tree_coor]['marker']['color'] = neighboring_node_color
    else:
        trace_dict[tree_coor]['marker']['color'] = stranger_node_color
        frames.append(go.Frame(data=updated_data, layout=go.Layout(annotations=[]), name='final'))

    return frames



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
    app.layout = html.Div(children=[
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
    # app.clientside_callback(
    #     ClientsideFunction(
    #         namespace='clientside',
    #         function_name='findSphereNeighbors'
    #     ),
    #     Output("sphere_neighbors_out", "children"),
    #     Output("kd-tree-sphere", "figure"),
    #     Input("kd-tree-sphere", "figure"),
    #     Input("traverse-button", "n_clicks"),
    #     State("a_val", "value"),
    #     State("b_val", "value"),
    #     State("c_val", "value"),
    #     State("r_val", "value"),
    # )
    # @app.server.route('/get_sphere_neighbors', methods=['POST'])
    # def get_sphere_neighbors():
    #     # Get the parameters from the request
    #     data = request.get_json()
    #     a = data.get('a')
    #     b = data.get('b')
    #     c = data.get('c')
    #     r = data.get('r')
        
    #     # Retrieve the cached KD tree
    #     tree = cache.get('kdtree')
        
    #     # Use the exact line you mentioned
    #     results, found, coordinates, inorder_neighbors = tree.find_sphere_neighbors(a,b,c,r)
        
    #     return jsonify({
    #         'results': results,
    #         'found': found,
    #         'coordinates': coordinates,
    #         'inorder_neighbors': inorder_neighbors
    #     })
# Run the app :D
    app.run_server(debug = False)

