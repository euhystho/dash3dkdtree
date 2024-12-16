// Ensure the namespace exists
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.clientside = window.dash_clientside.clientside || {};

window.dash_clientside.clientside.findSphereNeighbors = function(fig, clicks, a, b, c, r) {
// Check if the user has put values and clicked the button
    if (clicks > 0 && a && b && c && r){
    // Start by getting the tree json
        return fetch('/assets/tree_data.json')
            .then(response => response.json())
        //Extract the tree_structure to make it work with the javascript version of the python script
            .then(tree_structure => {
                const tree = new KDTree(tree_structure);
                let [results, found, coordinates, inorderNeighbors] = tree.findSphereNeighbors(a,b,c,r);

            // Create a deep copy of the plotly figure 
                let updatedFig = JSON.parse(JSON.stringify(fig));

            // Generates frames for the tree traversal
                updatedFig.frames = createTraversalAnimation(fig, coordinates, inorderNeighbors);

            // Remove all existing surface traces
                updatedFig.data = updatedFig.data.map(trace => {
                    if (trace.type === 'surface') {
                        return {...trace, visible: false};
                    }
                    return trace;
                });

            // Create the Sphere and add it to the figure data
                const sphere = createSphere(a, b, c, r);
                updatedFig.data.push(sphere);

            // Update layout with animation and spike settings
                updatedFig.layout = {
                    ...updatedFig.layout,
                // Spikes are intentionally turned off to minimized uncanny valley PLEASE DO NOT SWITCH TO TRUE ;-;
                    scene: {
                        ...(updatedFig.layout.scene || {}),
                        xaxis: { showspikes: false },
                        yaxis: { showspikes: false },
                        zaxis: { showspikes: false }
                    },
                // This stuff just creates the animation through plotly...
                    updatemenus: [{
                        buttons: [
                            {
                                args: [null, { frame: { duration: 1250, redraw: true }, fromcurrent: true }],
                                label: "Traverse Tree",
                                method: "animate"
                            },
                            {
                                args: [[null], { frame: { duration: 0, redraw: true }, mode: "immediate", transition: { duration: 0 } }],
                                label: "Pause Traversal",
                                method: "animate"
                            }
                        ],
                        direction: "left",
                        pad: { r: 10, t: 20 },
                        showactive: false,
                        type: "buttons",
                        x: 0.1,
                        xanchor: "right",
                        y: 0,
                        yanchor: "top"
                    }]
                };

            // Make the Text Pretty
                const neighbs = results.map(subArray => `(${subArray.join(', ')})`).join(', ');
            // If the center of the sphere is found we print out the corresponding text:
                const foundStatus = found ? "in the tree" : "not in the tree";
                let ret;
                
            //If we have results then we return that with a success Alert bootstrap class 
                if (results.length !== 0) {
                    ret = `The coordinate (${a}, ${b}, ${c}) is ${foundStatus} and its neighbors' coordinates are: ${neighbs}`;
                    createAlert(ret, "success");

            // Otherwise if the user has clearly inputted values but there are no results then there are no neighbors in the sphere
                } else if (a && b && c && r){
                    ret = "There are no neighbors in this sphere!";
                    createAlert(ret, "info")
                } 
                return updatedFig;
            })
        //Catching errors here :)
            .catch(error => {
                console.error('Error in findSphereNeighbors:', error);
                return fig;
            });
    }
// Returns Please Enter values...
    ret = "Please enter all coordinates and the radius...";
    alert = createAlert(ret, "warning")
    

    return fig;
};

function createSphere(a, b, c, r) {
// Not much to look here, same stuff as the python implementation
    const n = 50;
    const theta = Array.from({ length: n }, (_, i) => i * Math.PI / (n - 1));
    const phi = Array.from({ length: n }, (_, i) => i * 2 * Math.PI / (n - 1));

    const x = theta.map(t =>
        phi.map(p => r * Math.sin(t) * Math.cos(p) + a)
    );

    const y = theta.map(t =>
        phi.map(p => r * Math.sin(t) * Math.sin(p) + b)
    );

    const z = theta.map(t =>
        phi.map(() => r * Math.cos(t) + c)
    );

    const sphere = {
        type: 'surface',
        x: x,
        y: y,
        z: z,
        name: "sphere",
    //Cannot use Peach on Javascript ;-;
        colorscale: 'Cividis', 
        showscale: false,
        opacity: 0.5,
        contours: {
            x: { highlight: false },
            y: { highlight: false },
            z: { highlight: false }
        }
    };

    return sphere;
}

function createTraversalAnimation(fig, coors, neighbs) {
// Deep copy of input data
    const updatedFig = JSON.parse(JSON.stringify(fig));

// Ensure all scatter trace markers to black if the figure was used before :)
    updatedFig.data.forEach(trace => {
        if (trace.type === 'scatter' && trace.hoverinfo === 'text') {
            trace.marker = { 
                ...trace.marker, 
                color: 'black', 
                size: 15 
            };
        }
    });
    
// Separate scatter and surface traces
    const scatterList = updatedFig.data
        .filter(trace => trace.type === 'scatter')
        .map(trace => ({...trace}));
    
    const surfaceList = updatedFig.data
        .filter(trace => trace.type === 'surface')
        .map(trace => ({...trace}));

    const checkingNodeColor = 'orange';
    const neighboringNodeColor = 'green';
    const strangerNodeColor = 'red';

// Create frames for animation
    const frames = [];

//Create sets to keep track of the neighbors in the sphere and what nodes we already traversed
    var neighborNodes = new Set();
    var checkedNodes = new Set();

// Create trace dictionary for coordinate mapping for quick access (again like the python implementation)
    const traceDict = {};
    scatterList.forEach(trace => {
        if (trace.hoverinfo === 'text') {
            const coordinate = [trace.x[0], trace.y[0]];
            traceDict[coordinate] = {...trace, marker: {color: "black", size: 15}};
        }
    });


// Include 3D scatter plot points
    const pointsList = fig.data.filter(trace => trace.type === 'scatter3d');
    scatterList.push(...pointsList);
    
// Iterate through all the neighbors
    for (let i = 0; i < neighbs.length; i++) {
    // Create a deep copy of the 2D scatters that we are modifying
        var updatedData = JSON.parse(JSON.stringify(scatterList));

    // This value simply keeps the coordinate values according to if its in range of the coors array
        var coorsIterationValue;
    // treeCoor refers to the 2D Representation, graphCoor refers to the 3D Representation
        var treeCoor;
        var graphCoor;

    // Since the last frame is the last element of the neighbors, then we just check if the current value is the last frame
        var isLastFrame = i === neighbs.length - 1

    //Keep the coordinates in bounds if its the last frame
        if (isLastFrame){
            coorsIterationValue = coors.length - 1
            treeCoor = coors[coorsIterationValue][0];
            graphCoor = coors[coorsIterationValue][1];
        } else {
            coorsIterationValue = i
            treeCoor = coors[i][0];
            graphCoor = coors[i][1];
        }


    // Position calculations for arrow showing what's the current node
        let ax, ay;
        if (coorsIterationValue === 0) {
            [ax, ay] = [0, 75];  // Root
        } else if (coorsIterationValue % 2 === 0) {
            [ax, ay] = [-50, -40];  // Left
        } else {
            [ax, ay] = [50, -40];  // Right
        }

    // Get the plane with the corresponding node that is in the plane for the given coordinate
        let plane = null;
        surfaceList.forEach(surface => {
            const formattedGraphCoor = `(${graphCoor.join(', ')})`;
            if (surface.name === formattedGraphCoor) {
                surface.colorscale = 'Greys';
                surface.opacity = 1;
                plane = surface;
            }
        });
    // If we have successfully found the plane with right coordinate add it to the updatdData for the frame
        if (plane) updatedData.push(plane);

    //We go through all the traces of the updateData
        updatedData = updatedData.map(trace => {
        // Only modify scatter traces in 2D
            if (trace.type === 'scatter') {
              const coordinate = [trace.x[0], trace.y[0]];
              const coordinateKey = coordinate.join(',');
              
            // Check if this trace represents a node and not an edge
              const isTreeNode = coordinate.length === 2 && trace.hoverinfo === 'text';
              
              if (isTreeNode) {
            //Coloring Logic below YAY
                const isNodeBeingVisited = coordinateKey === treeCoor.join(',') && !isLastFrame
                const isNodeAlreadyNeighbor = neighborNodes.has(coordinateKey)
                const isNodeNeighbor = neighbs[i] && coordinateKey === neighbs[i].join(',')
                const isNodeStranger = checkedNodes.has(coordinateKey) && !neighborNodes.has(coordinateKey)

                if (isNodeBeingVisited) {
                    trace.marker = { ...trace.marker, color: checkingNodeColor };
                    checkedNodes.add(coordinateKey);
                } else if (isNodeAlreadyNeighbor) {
                  trace.marker = { ...trace.marker, color: neighboringNodeColor };
                } else if (isNodeNeighbor) {
                  trace.marker = { ...trace.marker, color: neighboringNodeColor };
                  neighborNodes.add(coordinateKey);
                } else if (isNodeStranger) {
                  trace.marker = { ...trace.marker, color: strangerNodeColor };
                }
              }
            }
            return trace;
          });

    // Create frame with updated data and arrow
        const frame = {
            data: updatedData,
            layout: {
                annotations: [{
                    x: treeCoor[0],
                    y: treeCoor[1],
                    ax: ax,
                    ay: ay,
                    xref: "x",
                    yref: "y",
                    text: "Current Node",
                    showarrow: true,
                    font: {size: 16, color: "#ff0000"},
                    arrowhead: 2,
                    arrowsize: 1,
                    arrowwidth: 3,
                    arrowcolor: "#ff0000",
                    opacity: 0.8
                }]
            },
            name: i === coors.length - 1 ? 'final' : `frame${i}`
        };
        
        frames.push(frame);
    }
    return frames;
}

function createAlert(message, type) {
// Create the bootstrap Alert using a div container
    const alertDiv = document.createElement('div');
//Set its attribute
    alertDiv.setAttribute('role', 'alert');
//Properly format the class name for the bootstrap based on the previous python implementation
    alertDiv.className = `fade alert alert-${type} show`;
//Text inside the div is the message to return
    alertDiv.innerText = message;

//NOTE: Please modify this value if going to a different HTML container
    //Find the container in the html file, which corresponds with the output div 
    const container = document.getElementById('sphere_neighbors_out')
    if (container){
    //If there was an existing bootstrap Alert, get replace it otherwise put the alert in the div container
        const existingAlert = container.querySelector('.alert');
        if (existingAlert){
            container.replaceChild(alertDiv,existingAlert)
        } else {
            container.appendChild(alertDiv);
        }

    } 
}

const LEVEL_DICT = {
    "X": 0,
    "Y": 1,
    "Z": 2
};

class KDTree {
    constructor(tree_structure){
    //Instead of this being none, it'll just be the tree_structure that was used in python...
        this.root = new KDNode(tree_structure.tree_structure);
    }

    find(a,b,c){
    //Code again similar to python implementaion
        if (this.root){
            var found = this.root.find(a,b,c)
        }
        return found
    }
    
    findSphereNeighbors(a,b,c,r,neighbors = [], traversalCoordinates = [], inorderNeighbors = [null]){
    //Code pretty similar to the Python implementation
        let isCenterFound = this.find(a,b,c)
        if (this.root){
            this.root.findSphereNeighbors(a,b,c,r,neighbors,traversalCoordinates,inorderNeighbors)
        // Remove the Center since its a neighbor of itself
            neighbors = neighbors.filter(subArray => !(subArray[0] === a && subArray[1] === b && subArray[2] === c));
            neighbors.sort()
        }
        return [neighbors, isCenterFound, traversalCoordinates, inorderNeighbors]
    }
};

class KDNode {
    constructor(data){
        this.x = data.x;
        this.y = data.y;
        this.z = data.z;
        this.inorderPos = data.inorder_pos;
        this.depth = data.depth;
        this.level = data.level;
        this.left = data.left ? new KDNode(data.left) : null;
        this.right = data.right ? new KDNode(data.right) : null;
    }

    find(x,y,z){
    //Code very similar to python implementation
        var ret = false
        if (this.x === x && this.y === y && this.z === z){
            ret = true
        }
        if (this.level === "X"){
            if (x < this.x && this.left){
                ret = this.left.find(x,y,z)
            } else if (x > this.x && this.right){
                ret = this.right.find(x,y,z)
            }
        } else if (this.level === "Y"){
            if (y < this.y && this.left){
                ret = this.left.find(x,y,z)
            } else if (y > this.y && this.right){
                ret = this.right.find(x,y,z)
            }
        } else if (this.level === "Z"){
            if (z < this.z && this.left){
                ret = this.left.find(x,y,z)
            } else if (z > this.z && this.right){
                ret = this.right.find(x,y,z)
            }
        }
        return ret
    }
    findSphereNeighbors(a,b,c,r,neighbors, traversalCoordinates, inorderNeighbors){
    // (All the following code is very similar to the python implementation)
    // Calculates the distance of the current node with the center of the sphere
        var distance = Math.sqrt(Math.pow(this.x - a, 2) + Math.pow(this.y - b, 2) + Math.pow(this.z - c,2))
    //  Checks to see if the center of the sphere is the current node
        var current_point = [this.x, this.y, this.z]
        var current_point_2D_val = [this.inorderPos, this.depth]
        var center_point = [a,b,c]
        var isCenter = current_point === center_point
    // Add the current coordinate to the traversal coordinates
        let coordinateList = [current_point_2D_val, current_point]
        traversalCoordinates.push(coordinateList)

        if (distance <= r){
            inorderNeighbors.push(current_point_2D_val)
            if (!isCenter){
                neighbors.push(current_point)
            }
        } else {
            inorderNeighbors.push(null)
        }

        var current_node_axis_value = current_point[LEVEL_DICT[this.level]]
        var center_axis_value = center_point[LEVEL_DICT[this.level]]

        if (center_axis_value < current_node_axis_value){
            if (this.left){
                this.left.findSphereNeighbors(a,b,c,r,neighbors,traversalCoordinates,inorderNeighbors)
            }
            if (Math.abs(center_axis_value - current_node_axis_value) <= r && this.right){
                this.right.findSphereNeighbors(a,b,c,r,neighbors,traversalCoordinates,inorderNeighbors)
            }
        } else {
            if (this.right){
                this.right.findSphereNeighbors(a,b,c,r,neighbors,traversalCoordinates,inorderNeighbors)
            }
            if (Math.abs(center_axis_value - current_node_axis_value) <= r && this.left){
                this.left.findSphereNeighbors(a,b,c,r,neighbors,traversalCoordinates,inorderNeighbors)
            }
        }

    }
};