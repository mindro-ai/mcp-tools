"""Generates a company structure diagram."""
import plotly.graph_objects as go

# --- Style Definitions ---
FOCUS_COMPANY_STYLE = {
    "fillcolor": "royalblue",
    "font": {"size": 14, "color": "white"}
}

DEFAULT_STYLE = {
    "fillcolor": "lightgrey",
    "font": {"size": 14, "color": "black"}
}

# --- Diagram Constants ---
# Layout
CANVAS_WIDTH = 12
LEVEL_HEIGHT = 3.5
NODE_WIDTH = 4
NODE_HEIGHT = 2
HORIZONTAL_GAP = 1.5
CONNECTOR_V_OFFSET = 1

# Figure
DIAGRAM_WIDTH_PX = 600
DIAGRAM_HEIGHT_PX = 500
MARGIN_PX = 10
X_AXIS_RANGE = [0, CANVAS_WIDTH]
Y_AXIS_RANGE = [-2, 10]


# --- Drawing Functions ---
def calculate_positions(companies_data):
    """
    Calculates the x, y positions for each company based on the hierarchy.
    Returns a dictionary of positions.
    """
    # Create a mutable copy to augment with child info
    data = {cid: cdata.copy() for cid, cdata in companies_data.items()}

    # Augment data with children and find root nodes
    roots = []
    for cid, cdata in data.items():
        cdata['children'] = []
    for cid, cdata in data.items():
        if not cdata.get("parents"):
            roots.append(cid)
        else:
            for parent_id in cdata["parents"]:
                if parent_id in data:
                    data[parent_id]['children'].append(cid)

    # Group companies by level using BFS
    levels = []
    queue = list(roots)
    visited = set(roots)
    while queue:
        levels.append(list(queue))
        next_level_queue = []
        for cid in queue:
            for child_id in data[cid].get('children', []):
                if child_id not in visited:
                    visited.add(child_id)
                    next_level_queue.append(child_id)
        queue = next_level_queue

    # Calculate positions based on levels
    positions = {}
    # Start y from the top, leaving space for the top-level nodes
    y_start = (len(levels) - 1) * LEVEL_HEIGHT

    for level_index, level_nodes in enumerate(levels):
        y = y_start - level_index * LEVEL_HEIGHT
        num_nodes = len(level_nodes)

        # Calculate positions to include horizontal spacing
        total_nodes_width = num_nodes * NODE_WIDTH
        total_gaps_width = max(0, num_nodes - 1) * HORIZONTAL_GAP
        total_level_width = total_nodes_width + total_gaps_width

        # Start from the left edge needed to center the group
        current_x = (CANVAS_WIDTH - total_level_width) / 2

        for node_id in level_nodes:
            # The center of the node is at current_x + half its width
            node_center_x = current_x + NODE_WIDTH / 2
            positions[node_id] = {'x': node_center_x, 'y': y, 'w': NODE_WIDTH, 'h': NODE_HEIGHT}

            # Move current_x for the next node
            current_x += NODE_WIDTH + HORIZONTAL_GAP

    return positions


def add_company(fig, pos, name, style):
    """Adds a company box and text to the figure."""
    x, y, w, h = pos['x'], pos['y'], pos['w'], pos['h']
    fig.add_shape(
        type="rect",
        x0=x - w/2, y0=y - h/2, x1=x + w/2, y1=y + h/2,
        line=dict(color="black", width=2),
        fillcolor=style["fillcolor"],
    )
    fig.add_annotation(
        x=x, y=y, text=name, showarrow=False,
        font=style["font"]
    )

def draw_connections(fig, companies_data, positions):
    """Draws lines between parent and child companies."""
    for company_id, company_data in companies_data.items():
        if not company_data.get("parents"):
            continue

        child_pos = positions[company_id]
        parent_ids = company_data["parents"]

        if len(parent_ids) == 1:
            # Case 1: Single parent. Draw a direct line.
            parent_pos = positions[parent_ids[0]]
            fig.add_shape(type="line",
                          x0=parent_pos['x'], y0=parent_pos['y'] - parent_pos['h']/2, # Bottom of parent
                          x1=child_pos['x'], y1=child_pos['y'] + child_pos['h']/2,   # Top of child
                          line=dict(color="black", width=2))
        else:
            # Case 2: Multiple parents. Use a horizontal connector.
            parent_positions = [positions[pid] for pid in parent_ids]
            parent_xs = [p['x'] for p in parent_positions]

            # Y-level for the horizontal connector line
            connector_y = child_pos['y'] + child_pos['h']/2 + CONNECTOR_V_OFFSET

            # Vertical lines from parents down to the connector
            for parent_pos in parent_positions:
                fig.add_shape(type="line",
                              x0=parent_pos['x'], y0=parent_pos['y'] - parent_pos['h']/2,
                              x1=parent_pos['x'], y1=connector_y,
                              line=dict(color="black", width=2))

            # Horizontal connector line
            fig.add_shape(type="line",
                          x0=min(parent_xs), y0=connector_y,
                          x1=max(parent_xs), y1=connector_y,
                          line=dict(color="black", width=2))

            # Vertical line from connector down to child
            fig.add_shape(type="line",
                          x0=child_pos['x'], y0=connector_y,
                          x1=child_pos['x'], y1=child_pos['y'] + child_pos['h']/2,
                          line=dict(color="black", width=2))


def generate_diagram(companies_data):
    """Creates and returns the company structure diagram."""
    fig = go.Figure()

    positions = calculate_positions(companies_data)

    # Add all companies to the figure by iterating through the data
    for company_id, company_data in companies_data.items():
        style = FOCUS_COMPANY_STYLE if company_data.get("focus") else DEFAULT_STYLE
        add_company(fig, positions[company_id], company_data["name"], style)

    # Add connecting lines based on the defined parent-child relationships
    draw_connections(fig, companies_data, positions)

    # Update layout
    fig.update_layout(
        xaxis=dict(visible=False, range=X_AXIS_RANGE),
        yaxis=dict(visible=False, range=Y_AXIS_RANGE), # Adjusted for new y-coords
        plot_bgcolor='white',
        width=DIAGRAM_WIDTH_PX,
        height=DIAGRAM_HEIGHT_PX,
        margin=dict(t=MARGIN_PX, b=MARGIN_PX, l=MARGIN_PX, r=MARGIN_PX)
    )
    return fig
