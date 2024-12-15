import math
import json
import numpy as np
import plotly.express as px
import plotly.graph_objects as go

from dash import dcc

# Necessary Global Variables, LEVEL variables are self explanatory for the coordinates
X_LEVEL = 'X'
Y_LEVEL = 'Y'
Z_LEVEL = 'Z'


LEVEL_DICT = {'X': 0, 'Y': 1, 'Z': 2}

# This is for the minimum and maximum overall value to get some space
EPSILON = 10


class KDTree:
    def __init__(self):
        self.root = None
        self.barriers = None
        self.list = []
        self.min_overall_val = None
        self.max_overall_val = None

    def add(self, x, y, z):
        """
        Adds Node to the KD Tree

        Args:
            x (float): an x-coordinate of the node to be added
            y (float): an y-coordinate of the node to be added
            z (float): an z-coordinate of the node to be added
        """
        if self.root:
            self.root.add(x,y,z)
        else:
            self.root = KDNode(x,y,z, X_LEVEL)
        # Set the Initial min and max overall values to the root's values
            self.min_overall_val = min(x,y,z) - EPSILON
            self.max_overall_val = max(x,y,z) + EPSILON
        
    def find(self, x, y, z):
        """
        Finds if the target node is in the Tree, records the path to the target node,
        along with the distance between the target node and the nodes traversed to the target node using the distance formula

        Args:
            x (float): an x-coordinate of the node to be found
            y (float): an y-coordinate of the node to be found
            z (float): an z-coordinate of the node to be found

        Returns:
            found (bool): True if the node is found in the tree, False otherwise
            path (dict): keys refer to the intermediary nodes between the root and the target node (2D Tree)
                              values refer to the distance between the intermediary nodes and the target node,
                              and the (x,y,z) coordinate in the 3D Tree
        """
    # Setup Structures beforehand...
        path = {}
        found = False

        if self.root:
            self.inorder()
            self.root.find_depths(0)
            found = self.root.find(x,y,z, path)
        else:
            dcc.ConfirmDialog(
                id = 'no-elements',
                message = 'There are no elements in the tree.'
            )
        
        return found, path
    
    def find_sphere_neighbors(self, a, b, c, r):
        """
        Finds the Sphere's neighbors that are within the sphere by checking each pole and the north, south, east, west of the equator

        Args:
            a (float): x-coordinate of the center of the sphere
            b (float): y-coordinate of the center of the sphere
            c (float): z-coordinate of the center of the sphere
            r (float): radius of the sphere

        Returns:
            neighbors (list): all the neighbors in the sphere
            isCenterFound (bool): True if the center of the sphere is in the tree, False otherwise
        """
    #Checks if the center of the sphere is in the tree
        isCenterFound, path = self.find(a,b,c)
        neighbors = []
        traversal_coordinates = []
    # We assume at the first part we do not know if it is in the neighbors yet so we start the first value as None
        inorder_neighbors = [None]
    # In Order and find_depths are simply there for Traversing the Tree :)
        if self.root:
            self.inorder()
            self.root.find_depths(0)
            self.root.find_sphere_neighbors(a,b,c,r, neighbors, traversal_coordinates, inorder_neighbors)
            neighbors.sort()
        return neighbors, isCenterFound, traversal_coordinates, inorder_neighbors
 
    def inorder(self):
        key_list = []
        if self.root:
            self.root.inorder([0], key_list)
        return key_list
    
    def draw(self, fig):
        """
        Draws the 2D and 3D Scatter Plots in Plotly along with the "barriers" (2D Plane)

        Returns:
            plotly figure: the figure that contains both the 2D and 3D Scatter Plots with the barriers
        """
        list = self.inorder()
        if self.root:
            self.root.draw(0, fig)
            self.barriers, fig = self.root.plot(list, fig)
        self.list = list
        return fig

# This method's main job is to export a json file of the tree for use on clientside callback:
    def to_dict(self):
        ret = None
        if self.root:
            self.inorder()
            self.root.find_depths(0)
            ret = self.root.to_dict()
        
        return ret
class KDNode:
    def __init__(self, x, y, z, level, parent = None):
        self.x = x
        self.y = y
        self.z = z
        self.inorder_pos = 0
        self.depth = 0
        self.level = level
        self.parent = parent
        self.left = None
        self.right = None

    def to_dict(self):
        ret = {
            "x": self.x,
            "y": self.y,
            "z": self.z,
            "inorder_pos": self.inorder_pos,
            "depth": self.depth,
            "level": self.level,
            "left": self.left.to_dict() if self.left else None,
            "right": self.right.to_dict() if self.right else None
        }
        return ret
    def add(self, x, y, z):
        """
        Recursively traverses through KDNodes, until there's a spot to add the node
        similar to other tree algorithms, except worrying about levels for the compare argument
        with each specific coordinate

        Args:
            x (float): an x-coordinate of the node to be added
            y (float): an y-coordinate of the node to be added
            z (float): an z-coordinate of the node to be added
        """
    
        if self.level == X_LEVEL:
            if x < self.x:
                if self.left:
                    self.left.add(x,y,z)
                else:
                    self.left = KDNode(x,y,z, Y_LEVEL, self)
            elif x > self.x:
                if self.right:
                    self.right.add(x,y,z)
                else:
                    self.right = KDNode(x,y,z, Y_LEVEL, self)
        elif self.level == Y_LEVEL:
            if y < self.y:
                if self.left:
                    self.left.add(x,y,z)
                else:
                    self.left = KDNode(x,y,z, Z_LEVEL, self)
            elif y > self.y:
                if self.right:
                    self.right.add(x,y,z)
                else:
                    self.right = KDNode(x,y,z, Z_LEVEL, self)
        elif self.level == Z_LEVEL:
            if z < self.z:
                if self.left:
                    self.left.add(x,y,z)
                else:
                    self.left = KDNode(x,y,z, X_LEVEL, self)                    
            elif z > self.z:
                if self.right:
                    self.right.add(x,y,z)
                else:
                    self.right = KDNode(x,y,z, X_LEVEL, self)

    def find(self, x, y, z, path):
        """
        Finds if the target node is in the Tree, records the path to the target node,
        along with the distance between the target node and the nodes traversed to the target node using the distance formula

        Args:
            x (float): an x-coordinate of the node to be found
            y (float): an y-coordinate of the node to be found
            z (float): an z-coordinate of the node to be found
            path (dict): records the root -> intermediary nodes -> target node

        Returns:
            bool: True if the node is found in the tree, False otherwise
        """
    # Assume innocent until proven guilty...
        ret = False
    # Add the current node to the path so far...
        tree_coordinates = (self.x,self.y, self.z)
        representation_coordinates = (self.inorder_pos, self.depth)
    # Using the Distance Formula on the current node and the target node
        distance = math.sqrt((self.x - x)**2 + (self.y - y)**2 + (self.z - z)**2)
        path[representation_coordinates] = (tree_coordinates, distance)
    # Checks if we have found the node if all coordinates match
        if self.x == x and self.y == y and self.z == z:
            ret = True
    # Continue traversing until we get closer to the target node:
    # Again, similar to the add function here:
        if self.level == X_LEVEL:
            if x < self.x and self.left:
                ret = self.left.find(x,y,z, path)
            elif x > self.x and self.right:
                ret = self.right.find(x,y,z, path)
        elif self.level == Y_LEVEL:
            if y < self.y and self.left:
                ret = self.left.find(x,y,z, path)
            elif y > self.y and self.right:
                ret = self.right.find(x,y,z, path)  
        elif self.level == Z_LEVEL:
            if z < self.z and self.left:
                ret = self.left.find(x,y,z, path)          
            elif z > self.z and self.right:
                ret = self.right.find(x,y,z, path)
        return ret

    def find_sphere_neighbors(self, a,b,c,r, neighbors, traversal_coordinates, inorder_neighbors):
        """
        Finds the Sphere's neighbors that are within the sphere by checking each pole and the north, south, east, west of the equator

        Args:
            a (float): x-coordinate of the center of the sphere
            b (float): y-coordinate of the center of the sphere
            c (float): z-coordinate of the center of the sphere
            r (float): radius of the sphere
            neighbors (list):  all the neighbors in the sphere

        """
    # Calculates the distance of the current node with the center of the sphere
        distance = math.sqrt((self.x - a)**2 + (self.y - b)**2 + (self.z - c)**2)
    # Checks to see if the center of the sphere is the current node
        current_point = (self.x, self.y, self.z)
        current_point_2D_val = (self.inorder_pos, self.depth)
        center_point = (a,b,c)
        isCenter = current_point == center_point

        traversal_coordinates.append([current_point_2D_val,current_point])

    #If it's a neighbor because the distance is in range of the sphere
        if distance <= r:
            inorder_neighbors.append(current_point_2D_val)
            if not isCenter:
                neighbors.append(current_point)
        else:
            inorder_neighbors.append(None)

    # Traverse based on the current level of the tree:
        current_node_axis_value = current_point[LEVEL_DICT[self.level]]
        center_axis_value = center_point[LEVEL_DICT[self.level]]
        
    #Based on the Tree Algorithm go the next applicable node:
        if center_axis_value < current_node_axis_value:
            if self.left:
                self.left.find_sphere_neighbors(a,b,c,r,neighbors, traversal_coordinates, inorder_neighbors)
            # Check the right subtree if it might contain closer neighbors:
            if abs(center_axis_value - current_node_axis_value) <= r and self.right:
                self.right.find_sphere_neighbors(a,b,c,r,neighbors, traversal_coordinates, inorder_neighbors)
        else:
            if self.right:
                self.right.find_sphere_neighbors(a,b,c,r,neighbors, traversal_coordinates, inorder_neighbors)
            # Check the left subtree if it might contain closer neighbors:
            if abs(center_axis_value - current_node_axis_value) <= r and self.left:
                self.left.find_sphere_neighbors(a,b,c,r,neighbors, traversal_coordinates, inorder_neighbors)
        
    def create_barrier(self, barrier_list, isLeft):
        """
        Creates the "barriers" for each node, which outlines the division between values smaller and larger than its respective level

        Args:
            barrier_list (list): records the surfaces so far for each node in the tree
            isLeft (bool): True if on the left side of the graph, False on the right side
        """
    #TODO: Change to the self.min_overall_value and self.max_overall_value to avoid magic numbers:
        min_x_val = min_y_val = min_z_val = 0
        max_x_val = max_y_val = max_z_val = 100
    # Checks if the Node has a parent at a certain level
        if self.parent:
            if self.parent.level == X_LEVEL:
            # Since the Node is at the Y-Level, you have to bound it to the X-Value of the parent
                if isLeft:
                    max_x_val = self.parent.x
                else:
                    min_x_val = self.parent.x

            elif self.parent.level == Y_LEVEL:
            # Bound the X Value to the last parent with an X-Level
                root = self.parent
                while root.parent and root.parent.level == X_LEVEL:
                    root = root.parent
            #Maintain the bound by the node's x-value
                if root.x < self.x:
                    min_x_val = root.x
                else:
                    max_x_val = root.x

            # Since the Node is at the Z-Level, you have to bound it to the Y-Value of the parent
                if isLeft:
                    max_y_val = self.parent.y
                else:
                    min_y_val = self.parent.y
            else:
            # Bound the Y Value to the last parent with an Y-Level
                root = self.parent
                while root.parent and root.parent.level == Y_LEVEL:
                    root = root.parent
            #Maintain the bound by the node's y-value
                if root.y < self.y:
                    min_y_val = root.y
                else:
                    max_y_val = root.y

            # Since the Node is at the X-Level, you have to bound it to the Z-Value of the parent
                if isLeft:
                    max_z_val = self.parent.z
                else:
                    min_z_val = self.parent.z

    # Start Creating the arrays to use for the plotly Surface object
        if self.level == X_LEVEL:
        # Create a surface perpendicular to X axis
            x = self.x * np.ones((2, 2))
            y = np.array([[min_y_val, max_y_val], [min_y_val, max_y_val]])
            z = np.array([[min_z_val, min_z_val], [max_z_val, max_z_val]])
            colorpalette = "Reds"
        elif self.level == Y_LEVEL:
        # Create a surface perpendicular to Y axis
            x = np.array([[min_x_val, min_x_val], [max_x_val, max_x_val]])
            y = self.y * np.ones((2, 2))
            z = np.array([[min_z_val, max_z_val], [min_z_val, max_z_val]])
            colorpalette = "Greens"
        else:
        # Create a surface perpendicular to Z axis
            x = np.array([[min_x_val, max_x_val], [min_x_val, max_x_val]])
            y = np.array([[min_y_val, min_y_val], [max_y_val, max_y_val]])
            z = self.z * np.ones((2, 2))
            colorpalette = "Teal"

    #Create the plotly graph object surface based on the arrays above,
        surf = go.Surface(
            x=x, 
            y=y, 
            z=z, 
            showscale=False, 
            colorscale=colorpalette,
            opacity=0.5, 
            visible=True,
            name = f"{(self.x,self.y,self.z)}"
        )
    # Add the surface to the barrier list to use later for the figure
        barrier_list.append(surf)

    #Continue iterating through the rest of the tree
        if self.left:
            self.left.create_barrier(barrier_list, isLeft = True)
        if self.right:
            self.right.create_barrier(barrier_list, isLeft = False)

    def inorder(self, num, key_list):
    # Taken from the inorder method of the other tree assignments, with a slight change
        if self.left:
            self.left.inorder(num, key_list)
        self.inorder_pos = num[0]
    #The key_list has a tuple of the (x,y,z) coordinates
        key_list.append((self.x,self.y,self.z))
        num[0] += 1
        if self.right:
            self.right.inorder(num, key_list)
    
    def find_depths(self,y):
        self.depth = y
        y_next = y - 1
        if self.left:
            self.left.find_depths(y_next)
        if self.right:
            self.right.find_depths(y_next)

    def draw(self, y, fig):
    # Similar to the draw method made in the 2D Tree assignment except using plotly instead of matplotlib
        x = self.inorder_pos
        self.depth = y

    # Basically Creates a point in the scatter plot with hover text that gives info about the node's coordinates and level
        fig.add_trace(go.Scatter(x = [x], y = [y], 
                                 mode = 'markers', 
                                 hovertext= f"{(self.x, self.y, self.z, self.level)}",
                                 hoverinfo = 'text',
                                 marker = dict(color = 'black',
                                               size = 15)))
        y_next = y-1
        if self.left:
            x_next = self.left.inorder_pos
    # Similar to the matplotlib but we "skip" the hoverinfo not to override the hoverinfo on the points
            fig.add_trace(go.Scatter(x = [x, x_next], y = [y, y_next], hoverinfo = 'skip', line = dict(color = 'black', width = 3)))
            fig.add_trace(go.Scatter(x = [x], y = [y], 
                            mode = 'markers', 
                            hovertext= f"{(self.x, self.y, self.z, self.level)}",
                            hoverinfo = 'text',
                            marker = dict(color = 'black',
                                          size = 15)))
            self.left.draw(y_next, fig)
        if self.right:
            x_next = self.right.inorder_pos
            fig.add_trace(go.Scatter(x = [x, x_next], y = [y, y_next], hoverinfo = 'skip', line = dict(color = 'black', width = 3)))
            fig.add_trace(go.Scatter(x = [x], y = [y], 
                mode = 'markers', 
                hovertext= f"{(self.x, self.y, self.z, self.level)}",
                hoverinfo = 'text',
                marker = dict(color = 'black',
                              size = 15)))
            self.right.draw(y_next, fig)

    def plot(self, list, fig):
        """
        Creates the 3D Plot Figure for the 3D KD Tree

        Args:
            list (list): the key_list used in the inorder that contains all the nodes' x, y, and z coordinates

        Returns:
            barriers (list): a list of plotly graph objects for the surfaces
            fig (plotly object): added data for the 3D Plot into the figure for plotly
        """
    # Arranges all the X, Y, Z values into lists to use for the scatter3d plot
        length = len(list)
        x_vals = [list[i][0] for i in range(length)]
        y_vals = [list[i][1] for i in range(length)]
        z_vals = [list[i][2] for i in range(length)]

        barriers = []
    # Create the Barriers, since we're starting at the root, we assume that isLeft is true,
        self.create_barrier(barriers,True)
    
        scatter = px.scatter_3d(x=x_vals, y=y_vals, z=z_vals, 
                                color_discrete_sequence = ['black'],
                                size_max=20, 
                                opacity=0.7)
    # Add the Scatter3D Plot as a trace to the figure
        fig.add_trace(scatter.data[0])

    # Add each barrier as a trace:
        for barrier in barriers:
            fig.add_trace(barrier)
        return barriers, fig
# Create the KDTree
tree = KDTree()
points = [
    [50, 50, 50],
    [25, 25, 25],
    [25, 50, 20],
    [25, 10, 10],
    [25, 10, 5],
    [25, 10, 20],
    [75, 75, 75],
    [75, 10, 5],
    [75, 100, 30],
    [75, 10, 20],
    [75, 10, 50],
    [75, 100, 70],
    [75, 100, 90]
]

for point in points:
    tree.add(point[0], point[1], point[2])

# Serialize the data
tree_data = {
    "tree_structure": tree.to_dict()  # Serialize the tree structure
}

# Save the serialized data to a JSON file
with open('assets/tree_data.json', 'w') as f:
    json.dump(tree_data, f)
