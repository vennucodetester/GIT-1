# Draggable Sensor Labels - Implementation Guide

## Overview
This guide explains how to port the draggable sensor labels feature from GIT-1 to DIAGNOSTIC TOOL.

## Branch Information
**Branch Name:** `claude/draggable-sensor-labels-011CUqy8SDfEamYdggyKzRPV`

**Commits:**
1. `616d3fc` - Implement draggable sensor labels with persistent offsets
2. `9f64a10` - Add .gitignore to exclude Python cache files and other artifacts

## Files Modified
- `diagram_components.py` - Main implementation file

---

## Changes to Port

### 1. Add DraggableTextItem Class
**Location:** Insert before `SensorBoxItem` class (around line 1819 in GIT-1)

**Source:** `diagram_components.py` lines 1819-1889

```python
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
```

---

### 2. Add save_label_offset Method to SensorBoxItem
**Location:** Inside `SensorBoxItem` class, after `edit_title()` method (around line 2097)

**Source:** `diagram_components.py` lines 2097-2122

```python
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
```

---

### 3. Update create_sensor_row Method
**Location:** Replace entire `create_sensor_row()` method in `SensorBoxItem` class

**Key Changes:**
1. Load stored offsets from `box_data` (lines 2009-2025)
2. Define default offsets (lines 2017-2020)
3. Replace `QGraphicsTextItem` with `DraggableTextItem` for:
   - `label_item` (line 2029)
   - `number_item` (line 2039)
   - `value_item` (line 2054)
4. Apply offsets when positioning items

**Full Method (lines 1979-2060):**

```python
def create_sensor_row(self, x, y, sensor_id, sensor_info):
    """Create one sensor's row with three columns: dot+label | number | value."""
    role_key = sensor_info['role_key']

    # Check if mapped
    mapped_sensor = self.data_manager.get_mapped_sensor_for_role(role_key) if self.data_manager else None
    is_selected = mapped_sensor and mapped_sensor in self.data_manager.selected_sensors if self.data_manager else False

    # Create dot (square for sensor box)
    if is_selected:
        dot_color = QColor('#FF0000')  # Red for selected
        pen_width = 3
    elif mapped_sensor:
        dot_color = QColor('#4CAF50')  # Green for mapped
        pen_width = 2
    else:
        dot_color = QColor('#FF6B00')  # Orange for unmapped
        pen_width = 2

    dot = QGraphicsRectItem(-6, -6, 12, 12, self)
    dot.setBrush(QBrush(dot_color))
    dot.setPen(QPen(Qt.GlobalColor.black, pen_width))
    dot.setPos(x, y)
    dot.setZValue(100)
    dot.setCursor(Qt.CursorShape.PointingHandCursor)
    dot.setData(0, role_key)
    dot.setData(1, 'sensor_box')
    dot.setData(2, sensor_id)
    sensor_info['dot'] = dot

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

    # Create label item (right of dot in column 1) - now draggable
    label_text = sensor_info['label']
    label_item = DraggableTextItem(label_text, self, self, sensor_id, 'label')
    label_item.setDefaultTextColor(QColor("#000000"))
    label_item.setPos(x + label_offset['dx'], y + label_offset['dy'])
    sensor_info['label_item'] = label_item

    # Create number item (column 2) - now draggable
    number_text = ""
    if mapped_sensor:
        num = self.data_manager.get_sensor_number(mapped_sensor)
        number_text = f"#{num}" if num is not None else ""
    number_item = DraggableTextItem(number_text, self, self, sensor_id, 'number')
    number_item.setDefaultTextColor(QColor("#000000"))
    number_item.setPos(x + number_offset['dx'], y + number_offset['dy'])
    sensor_info['number_item'] = number_item

    # Create value item (column 3) - now draggable
    value_text = ""
    if mapped_sensor:
        val = self.data_manager.get_sensor_value(mapped_sensor)
        if val is None:
            value_text = ""
        elif isinstance(val, (int, float)):
            value_text = f"{val:.1f}"
        else:
            value_text = str(val)
    value_item = DraggableTextItem(value_text, self, self, sensor_id, 'value')
    value_item.setDefaultTextColor(QColor("#000000"))
    value_item.setPos(x + value_offset['dx'], y + value_offset['dy'])
    sensor_info['value_item'] = value_item

    # Store in sensors dict
    self.sensors[sensor_id] = sensor_info
```

---

## Implementation Steps for DIAGNOSTIC TOOL

1. **Backup your current `diagram_components.py`**
   ```bash
   cp diagram_components.py diagram_components.py.backup
   ```

2. **Add DraggableTextItem class**
   - Find the line where `SensorBoxItem` class is defined
   - Insert the entire `DraggableTextItem` class before it

3. **Add save_label_offset method**
   - Find the `edit_title()` method in `SensorBoxItem` class
   - Add the `save_label_offset()` method right after it

4. **Replace create_sensor_row method**
   - Find the existing `create_sensor_row()` method
   - Replace it entirely with the new version above

5. **Test the implementation**
   - Open a sensor box
   - Try dragging sensor labels, numbers, and values
   - Verify positions are saved when you close and reopen the diagram

---

## Data Structure Changes

The implementation adds an `offsets` dictionary to each sensor in `box_data`:

```python
sensor = {
    'id': 'sensor_abc123',
    'label': 'Temperature Sensor',
    'offsets': {
        'label': {'dx': 15, 'dy': -8},
        'number': {'dx': 150, 'dy': -8},
        'value': {'dx': 210, 'dy': -8}
    }
}
```

This structure ensures:
- Positions are relative to the sensor dot
- Labels maintain their offset when the sensor box moves
- Offsets persist across application restarts

---

## Expected Behavior

After implementation:
1. **Hover**: Cursor changes to open hand over labels
2. **Click**: Cursor changes to closed hand, label is "picked up"
3. **Drag**: Label follows mouse cursor
4. **Release**: Label position is saved, cursor returns to open hand
5. **Persistence**: Custom positions are restored when diagram is reopened

---

## Troubleshooting

**Labels don't move:**
- Verify `DraggableTextItem` is imported/defined
- Check that `create_sensor_row` uses `DraggableTextItem` instead of `QGraphicsTextItem`

**Positions not saved:**
- Verify `save_label_offset()` method exists in `SensorBoxItem`
- Check that `data_manager.save_diagram()` is being called

**Labels reset to default position:**
- Verify offset loading logic in `create_sensor_row` (lines 2009-2025)
- Check that `box_data['sensors']` contains `offsets` dictionary

---

## Files Reference

**GIT-1 Branch:** `claude/draggable-sensor-labels-011CUqy8SDfEamYdggyKzRPV`

**Modified File:** `diagram_components.py`
- DraggableTextItem class: lines 1819-1889
- save_label_offset method: lines 2097-2122
- create_sensor_row method: lines 1979-2060
