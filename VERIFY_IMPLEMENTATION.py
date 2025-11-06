"""
VERIFICATION FILE - This shows EXACTLY what is in diagram_components.py
If you don't see this code in your downloaded file, GitHub Desktop failed to sync.
"""

# ==============================================================================
# 1. DraggableTextItem CLASS - Should be at line 1819
# ==============================================================================

class DraggableTextItem(QGraphicsTextItem):
    """A text item that can be dragged and maintains offset from parent sensor dot."""

    def __init__(self, text, parent, sensor_box, sensor_id, item_type):
        """
        Initialize draggable text item.

        Args:
            text: The text to display
            parent: The parent QGraphicsItem
            sensor_box: The SensorBoxItem this belongs to
            sensor_id: The sensor ID this text belongs to
            item_type: Type of item ('label', 'number', or 'value')
        """
        super().__init__(text, parent)
        self.sensor_box = sensor_box
        self.sensor_id = sensor_id
        self.item_type = item_type
        self.is_dragging = False
        self.drag_start_pos = None

        # Make the item movable
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsMovable, True)
        self.setFlag(QGraphicsItem.GraphicsItemFlag.ItemIsSelectable, True)
        self.setCursor(Qt.CursorShape.OpenHandCursor)

    def mousePressEvent(self, event):
        """Handle mouse press - start dragging."""
        if event.button() == Qt.MouseButton.LeftButton:
            self.is_dragging = True
            self.drag_start_pos = self.pos()
            self.setCursor(Qt.CursorShape.ClosedHandCursor)
            event.accept()
        else:
            super().mousePressEvent(event)

    def mouseMoveEvent(self, event):
        """Handle mouse move - update position while dragging."""
        if self.is_dragging:
            # Let the default movement happen
            super().mouseMoveEvent(event)
            event.accept()
        else:
            super().mouseMoveEvent(event)

    def mouseReleaseEvent(self, event):
        """Handle mouse release - finish dragging and save offset."""
        if event.button() == Qt.MouseButton.LeftButton and self.is_dragging:
            self.is_dragging = False
            self.setCursor(Qt.CursorShape.OpenHandCursor)

            # Calculate offset from dot position
            if self.sensor_id in self.sensor_box.sensors:
                sensor_info = self.sensor_box.sensors[self.sensor_id]
                dot = sensor_info.get('dot')
                if dot:
                    # Get current position relative to parent (the sensor box)
                    current_pos = self.pos()
                    dot_pos = dot.pos()

                    # Calculate offset from dot
                    dx = current_pos.x() - dot_pos.x()
                    dy = current_pos.y() - dot_pos.y()

                    # Save the offset
                    self.sensor_box.save_label_offset(self.sensor_id, self.item_type, dx, dy)

            event.accept()
        else:
            super().mouseReleaseEvent(event)


# ==============================================================================
# 2. save_label_offset METHOD - Should be at line 2115 in SensorBoxItem class
# ==============================================================================

def save_label_offset(self, sensor_id, item_type, dx, dy):
    """
    Save the offset for a label relative to its dot.

    Args:
        sensor_id: The sensor ID
        item_type: Type of item ('label', 'number', or 'value')
        dx: X offset from dot
        dy: Y offset from dot
    """
    # Find the sensor in box_data
    if 'sensors' in self.box_data:
        for sensor in self.box_data['sensors']:
            if sensor['id'] == sensor_id:
                # Initialize offsets dict if it doesn't exist
                if 'offsets' not in sensor:
                    sensor['offsets'] = {}

                # Store the offset
                sensor['offsets'][item_type] = {'dx': dx, 'dy': dy}

                # Update in data manager if available
                if self.data_manager:
                    self.data_manager.save_diagram()

                break


# ==============================================================================
# 3. PROOF OF DraggableTextItem USAGE - Lines 2029, 2039, 2054
# ==============================================================================

# Line 2029 - label_item uses DraggableTextItem
label_item = DraggableTextItem(label_text, self, self, sensor_id, 'label')

# Line 2039 - number_item uses DraggableTextItem  
number_item = DraggableTextItem(number_text, self, self, sensor_id, 'number')

# Line 2054 - value_item uses DraggableTextItem
value_item = DraggableTextItem(value_text, self, self, sensor_id, 'value')


# ==============================================================================
# 4. PROOF OF OFFSET LOADING - Lines 2009-2025
# ==============================================================================

# Load stored offsets from box_data
stored_offsets = {}
if 'sensors' in self.box_data:
    for sensor in self.box_data['sensors']:
        if sensor['id'] == sensor_id:
            stored_offsets = sensor.get('offsets', {})
            break

# Default offsets if not stored
default_label_offset = {'dx': 15, 'dy': -8}
default_number_offset = {'dx': self.COL2_X - x, 'dy': -8}
default_value_offset = {'dx': self.COL3_X - x, 'dy': -8}

# Get offsets (use stored or default)
label_offset = stored_offsets.get('label', default_label_offset)
number_offset = stored_offsets.get('number', default_number_offset)
value_offset = stored_offsets.get('value', default_value_offset)

