window.dash_clientside = window.dash_clientside || {};
window.dash_clientside.clientside = {
    findSphereNeighbors: function(fig, clicks, a, b, c, r) {
        // Check if inputs are valid
        if (clicks > 0 && a !== null && b !== null && c !== null && r !== null) {
            // Return a promise that resolves with the server's response
            return fetch('/get_sphere_neighbors', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({a, b, c, r})
            })
            .then(response => response.json())
            .then(data => {
                
                // Destructure the data from the server
                const { results, found, coordinates, inorder_neighbors } = data;

                // Prepare alert message
                let alertMessage = "There are no neighbors in this sphere!";
                let alertType = "info";

                if (results.length > 0) {
                    const neighbs = results.map(result => result.toString()).join(", ");
                    const foundStatus = found ? "in the tree" : "not in the tree";
                    alertMessage = `The coordinate (${a},${b},${c}) is ${foundStatus} and its neighbors' coordinates are: ${neighbs}`;
                    alertType = "success";
                }

                const alert = {
                    component: 'Alert',
                    props: {
                        children: alertMessage,
                        color: alertType === 'success' ? 'success' : 'info'
                    }
                };

                // Create frames for animation
                const frames = coordinates.map((coord, index) => ({
                    name: `frame${index}`,
                    data: fig.data.map(trace => {
                        const newTrace = {...trace};
                        // Change color of neighboring points
                        if (newTrace.type === 'scatter' && 
                            newTrace.x && newTrace.x.length > 0 && 
                            newTrace.x[0] === coord[0] && 
                            newTrace.y[0] === coord[1]) {
                            newTrace.marker = {
                                ...newTrace.marker,
                                color: inorder_neighbors[index] ? 'green' : 'red'
                            };
                        }
                        return newTrace;
                    }),
                    layout: fig.layout
                }));

                // Update the figure to add a sphere
                const newFig = {...fig};
                
                // Create sphere surface
                const n = 50;
                const theta = Array.from({length: n}, (_, i) => i * Math.PI / (n-1));
                const phi = Array.from({length: n}, (_, i) => i * 2 * Math.PI / (n-1));
                
                const x = theta.flatMap(t => phi.map(p => r * Math.sin(t) * Math.cos(p) + a));
                const y = theta.flatMap(t => phi.map(p => r * Math.sin(t) * Math.sin(p) + b));
                const z = theta.flatMap(t => phi.map(p => r * Math.cos(t) + c));

                const sphereSurface = {
                    type: 'surface',
                    x: x,
                    y: y,
                    z: z,
                    colorscale: 'Peach',
                    showscale: false,
                    opacity: 0.5
                };

                newFig.data = [...newFig.data, sphereSurface];
                newFig.frames = frames;
                console.log(newFig)
                return [alert, newFig];
            });
        }
        
        // Default return if inputs are not valid
        return [
            {
                component: 'Alert',
                props: {
                    children: 'Please enter all coordinates and the radius...',
                    color: 'warning'
                }
            },
            fig
        ];
    }
};