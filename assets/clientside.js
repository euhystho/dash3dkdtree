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

                // Create a deep copy of the figure to avoid direct mutation
                let updatedFig = JSON.parse(JSON.stringify(fig));

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

                // Regenerate frames for tree traversal
                updatedFig.frames = createTraversalAnimation(updatedFig, coordinates, inorderNeighbors);
                
                // Make the Text Pretty
                const neighbs = results.map(subArray => `(${subArray.join(',')})`).join(', ');
                const foundStatus = found ? "in the tree" : "not in the tree";
                let ret;
                
                if (results.length !== 0) {
                    ret = `The coordinate (${a},${b},${c}) is ${foundStatus} and its neighbors' coordinates are: ${neighbs}`;
                } else {
                    ret = "Please enter all coordinates and the radius...";
                }
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

function createTraversalAnimation(fig, coors, neighbs) {
    const scatterList = fig.data.filter(trace => trace.type === 'scatter').map(trace => ({...trace}));
    const surfaceList = fig.data.filter(trace => trace.type === 'surface').map(trace => ({...trace}));
    const checkingNodeColor = 'orange';
    const neighboringNodeColor = 'green';
    const strangerNodeColor = 'red';

    // Create a list of frames for the animation
    const frames = [];

    // Create a dictionary to map the coordinates with the traces
    const traceDict = {};
    scatterList.forEach(trace => {
        if (trace.hoverinfo === 'text') {
            const coordinate = [trace.x[0], trace.y[0]];
            traceDict[coordinate] = trace;
        }
    });

    const seenNeighbors = new Set();

    const pointsList = fig.data.filter(trace => trace.type === 'scatter3d').map(trace => ({...trace}));
    scatterList.push(...pointsList);
    
    for (let i = 0; i < coors.length; i++) {
        updatedData = [...scatterList];
        // Calculate ax based on the position in the tree
        let ax, ay;
        if (i === 0) {
            [ax, ay] = [0, 75];  // Root
        } else if (i % 2 === 0) {
            [ax, ay] = [-50, -40];  // Left
        } else {
            [ax, ay] = [50, -40];  // Right
        }
        
        treeCoor = coors[i][0];
        const graphCoor = coors[i][1];

        let plane = null;
        for (const surface of surfaceList) {
            if (surface.name === graphCoor.toString()) {
                surface.colorscale = "gray";
                surface.opacity = 1;
                plane = surface;
                break;
            }
        }

        updatedData.push(plane);

        // Update the color of the corresponding trace
        if (treeCoor in traceDict) {
            traceDict[treeCoor].marker.color = checkingNodeColor;
        }

        if (neighbs[i]) {
            const coord = neighbs[i];
            if (coord in traceDict) {
                traceDict[coord].marker.color = neighboringNodeColor;
                seenNeighbors.add(coord);
            }
        }

        for (const [coord, trace] of Object.entries(traceDict)) {
            if (coord !== treeCoor && trace.marker.color === checkingNodeColor) {
                traceDict[coord].marker.color = strangerNodeColor;
            }
        }

        // Create a frame with the updated trace and the arrow annotation
        const frame = {
            data: updatedData,
            layout: {
                annotations: [
                    {
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
                    }
                ]
            },
            name: `frame${i}`
        };
        frames.push(frame);
    }

    // Check Final Value:
    if (treeCoor === neighbs[neighbs.length - 1]) {
        traceDict[treeCoor].marker.color = neighboringNodeColor;
    } else {
        traceDict[treeCoor].marker.color = strangerNodeColor;
        frames.push({data: updatedData, layout: {annotations: []}, name: 'final'});
    }

    return frames;
};

function createSphere(a, b, c, r) {
    // Points in the Meshgrid
    const n = 50;

    // Using the Formula of a sphere below:
    const theta = Array.from({length: n}, (_, i) => i * Math.PI / (n - 1));
    const phi = Array.from({length: n}, (_, i) => i * 2 * Math.PI / (n - 1));

    const x = new Array(n).fill().map(() => new Array(n));
    const y = new Array(n).fill().map(() => new Array(n));
    const z = new Array(n).fill().map(() => new Array(n));

    for (let i = 0; i < n; i++) {
        for (let j = 0; j < n; j++) {
            x[i][j] = r * Math.sin(theta[i]) * Math.cos(phi[j]) + a;
            y[i][j] = r * Math.sin(theta[i]) * Math.sin(phi[j]) + b;
            z[i][j] = r * Math.cos(theta[i]) + c;
        }
    }

    // Put the arrays into a surface to display it in plotly :)
    const sphere = {
        type: 'surface',
        x: x,
        y: y,
        z: z,
        name: "sphere",
        colorscale: 'Peach',
        opacity: 0.5,
        showscale: false,

        // PLEASE DO NOT TURN THIS TO TRUE D:
        // Turning off contours is good for your sanity... (it removes lines that contour around the sphere,
        // If you keep dragging the sphere around with these turned on, it gives you tons of lines around the sphere
        contours: {
            x: {highlight: false},
            y: {highlight: false},
            z: {highlight: false}
        }
    };

    return sphere;
};