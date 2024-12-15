// Ensure the namespace exists
window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.clientside = window.dash_clientside.clientside || {};

window.dash_clientside.clientside.findSphereNeighbors = function(fig, clicks, a, b, c, r) {
    // Check if the user has put values and clicked the button
    if (clicks > 0 && a && b && c && r){
        // Start by getting the tree
        return fetch('/assets/tree_data.json')
            .then(response => response.json())
            .then(tree_structure => {
                const tree = new KDTree(tree_structure);
                let [results, found, coordinates, inorderNeighbors] = tree.findSphereNeighbors(a,b,c,r);

                // Create a deep copy of the figure 
                let updatedFig = JSON.parse(JSON.stringify(fig));

                // Regenerate frames for tree traversal
                updatedFig.frames = createTraversalAnimation(fig, coordinates, inorderNeighbors);

                // Remove all surface traces
                updatedFig.data = updatedFig.data.map(trace => {
                    if (trace.type === 'surface') {
                        return {...trace, visible: false};
                    }
                    return trace;
                });

                // Create the Sphere and add it to the figure
                const sphere = createSphere(a, b, c, r);
                updatedFig.data.push(sphere);

                // Update layout with animation and spike settings
                updatedFig.layout = {
                    ...updatedFig.layout,
                    scene: {
                        ...(updatedFig.layout.scene || {}),
                        xaxis: { showspikes: false },
                        yaxis: { showspikes: false },
                        zaxis: { showspikes: false }
                    },
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
                const neighbs = results.map(subArray => `(${subArray.join(',')})`).join(', ');
                const foundStatus = found ? "in the tree" : "not in the tree";
                let alert;
                let ret;
                
                if (results.length !== 0) {
                    ret = `The coordinate (${a},${b},${c}) is ${foundStatus} and its neighbors' coordinates are: ${neighbs}`;
                    alert = createAlert(ret, "success");
                } else if (a && b && c && r){
                    ret = "There are no neighbors in this sphere!";
                    alert = createAlert(ret, "info")
                } else {
                    ret = "Please enter all coordinates and the radius...";
                    alert = createAlert(ret, "warning")
                }
                console.log('Return values is', alert)

                return [ret, updatedFig];
            })
            .catch(error => {
                console.error('Error in findSphereNeighbors:', error);
                return [null, fig];
            });
    }
    
    // Return default values if conditions are not met
    return [null, fig];
};

function createSphere(a, b, c, r) {
    // Points in the Meshgrid
    const n = 50;

    // Using the spherical coordinate system approach similar to NumPy
    const theta = Array.from({length: n}, (_, i) => i * Math.PI / (n - 1));
    const phi = Array.from({length: n}, (_, i) => i * 2 * Math.PI / (n - 1));

    // Create meshgrid-like arrays
    const x = theta.map(t => 
        phi.map(p => r * Math.sin(t) * Math.cos(p) + a)
    );
    
    const y = theta.map(t => 
        phi.map(p => r * Math.sin(t) * Math.sin(p) + b)
    );
    
    const z = theta.map(t => 
        phi.map(() => r * Math.cos(t) + c)
    );

    // Put the arrays into a surface to display it in plotly
    const sphere = {
        type: 'surface',
        x: x,
        y: y,
        z: z,
        name: "sphere",
        opacity: 0.5,
        showscale: false,
        contours: {
            x: {highlight: false},
            y: {highlight: false},
            z: {highlight: false}
        }
    };

    return sphere;
}

function createTraversalAnimation(fig, coors, neighbs) {
    // Deep copy of input data
    const updatedFig = JSON.parse(JSON.stringify(fig));
    
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
    var neighborNodes = new Set();
    var checkedNodes = new Set();

    // Create trace dictionary for coordinate mapping
    const traceDict = {};
    scatterList.forEach(trace => {
        if (trace.hoverinfo === 'text') {
            const coordinate = [trace.x[0], trace.y[0]];
            traceDict[coordinate] = {...trace, marker: {color: "black", size: 15}};
        }
    });


    // Include 3D points
    const pointsList = fig.data.filter(trace => trace.type === 'scatter3d');
    scatterList.push(...pointsList);
    
    for (let i = 0; i < coors.length; i++) {
        var updatedData = JSON.parse(JSON.stringify(scatterList));
        
        // Position calculation for annotation arrow
        let ax, ay;
        if (i === 0) {
            [ax, ay] = [0, 75];  // Root
        } else if (i % 2 === 0) {
            [ax, ay] = [-50, -40];  // Left
        } else {
            [ax, ay] = [50, -40];  // Right
        }
        
        const treeCoor = coors[i][0];
        const graphCoor = coors[i][1];

        // Update surface plane
        let plane = null;
        surfaceList.forEach(surface => {
            const formattedGraphCoor = `(${graphCoor.join(', ')})`;
            if (surface.name === formattedGraphCoor) {
                surface.colorscale = "gray";
                surface.opacity = 1;
                plane = surface;
            }
        });

        if (plane) updatedData.push(plane);

        updatedData = updatedData.map(trace => {
            // Only modify scatter traces
            if (trace.type === 'scatter') {
              const coordinate = trace.x.length === 1 ? [trace.x[0], trace.y[0]] : [trace.x[0], trace.y[0]];
              const coordinateKey = coordinate.join(',');
              
              // Check if this trace represents a tree node
              const isTreeNode = coordinate.length === 2 && trace.hoverinfo === 'text';
              
              if (isTreeNode) {
                const strangerNodes = new Set([...checkedNodes].filter(element => !neighborNodes.has(element)));
                console.log(strangerNodes, neighborNodes);
                
                // Prioritize coloring logic
                if (coordinateKey === treeCoor.join(',')) {
                    checkedNodes.add(coordinateKey);
                } else if (neighborNodes.has(coordinateKey)) {
                  trace.marker = { ...trace.marker, color: neighboringNodeColor };
                } else if (neighbs[i] && coordinateKey === neighbs[i].join(',')) {
                  trace.marker = { ...trace.marker, color: neighboringNodeColor };
                  neighborNodes.add(coordinateKey);
                } else if (strangerNodes.has(coordinateKey)) {
                  trace.marker = { ...trace.marker, color: strangerNodeColor };
                }
              }
            }
            return trace;
          });

        // Create frame with updated data and annotation
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
            name: `frame${i}`
        };
        
        frames.push(frame);
    }

    // Final frame processing
    const lastTreeCoor = coors[coors.length - 1][0];
    const lastNeighbor = neighbs[neighbs.length - 1];
    
    if (lastTreeCoor === lastNeighbor) {
        traceDict[lastTreeCoor].marker.color = neighboringNodeColor;
    } else {
        traceDict[lastTreeCoor].marker.color = strangerNodeColor;
        frames.push({
            data: updatedData, 
            layout: {annotations: []}, 
            name: 'final'
        });
    }
    return frames;
}

function createAlert(message, type) {
    // Create the alert div
    const alertDiv = document.createElement('div');
    alertDiv.className = `alert alert-${type}`;
    alertDiv.role = 'alert';
    alertDiv.innerText = message;
    return alertDiv;
}

const LEVEL_DICT = {
    "X": 0,
    "Y": 1,
    "Z": 2
};

class KDTree {
    constructor(tree_structure){
        this.root = new KDNode(tree_structure.tree_structure);
    }

    find(a,b,c){
        if (this.root){
            var found = this.root.find(a,b,c)
        }
        return found
    }
    
    findSphereNeighbors(a,b,c,r,neighbors = [], traversalCoordinates = [], inorderNeighbors = [null]){
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