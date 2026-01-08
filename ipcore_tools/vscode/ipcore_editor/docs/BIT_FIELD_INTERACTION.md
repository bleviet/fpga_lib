# Shift-Drag Bit Field Interaction: Implementation Details

This document details the mathematical and programmatic implementation of the "Shift-Drag" interaction within the `BitFieldVisualizer` component. This feature allows users to resize existing bit fields and create new ones by dragging across the visual register grid.

## 1. Core Architecture

The visualization is built on a "Pro Segment" model which converts the abstract list of fields into a linear, rendered representation of the register.

### Data Structures

#### The `bits` Lookup Array
A dense array mapping every bit index (0-31) to a field index.
```typescript
const bits: (number | null)[] = Array(registerSize).fill(null);
// If bits[5] === 0, it means bit 5 belongs to fields[0].
// If bits[5] === null, bit 5 is a gap.
```
This array is recalculated on every render and serves as the primary collision map for hit-testing.

#### The Segment Model (`buildProLayoutSegments`)
Instead of rendering fields directly, the Pro Layout renders a list of **Segments**. A segment works like a "span" in the UI.

1.  **Input**: List of `Field` objects (arbitrary order).
2.  **Process**:
    *   Sort fields by MSB (descending).
    *   Iterate from `registerSize - 1` down to `0`.
    *   If the cursor is at a bit occupied by a field, push a `FieldSegment`.
    *   If the cursor is at an empty bit, identify the contiguous empty region and push a `GapSegment`.
3.  **Output**: An ordered list of segments covering the full 32-bit range.

```typescript
type ProSegment =
  | { type: 'field'; idx: number; start: number; end: number; ... }
  | { type: 'gap'; start: number; end: number };
```

**Why this matters**: This approach reifies "empty space" into DOM elements (`GapSegment`), making them interactive target that can listen for `pointerdown` events.

---

## 2. Interaction State Machine

The interaction is managed by the `shiftDrag` state object:

```typescript
interface ShiftDragState {
  active: boolean;              // Is a drag defined?
  mode: 'resize' | 'create';    // Operation type
  targetFieldIndex: number;     // (Resize only) Which field is being modified
  anchorBit: number;            // Where the user pressed pointer down
  currentBit: number;           // Where the user's pointer currently is (clamped)
  minBit: number;               // Hard lower limit (collision boundary)
  maxBit: number;               // Hard upper limit (collision boundary)
}
```

### State Transitions

1.  **Idle**: `active: false`.
2.  **Pointer Down (Shift Key Held)**:
    *   **Hit Test**: Check `bits[clickedBit]`.
    *   If **Hit Field** -> **Resize Mode**:
        *   Target: Field at index.
        *   Boundaries: Calculated via `findResizeBoundary`.
    *   If **Hit Gap** -> **Create Mode**:
        *   Boundaries: Calculated via `findGapBoundaries`.
3.  **Pointer Move**:
    *   Update `currentBit`.
    *   **Constraint**: `currentBit = clamp(rawBit, minBit, maxBit)`.
    *   This ensures the user cannot drag "through" an existing field into another one.
4.  **Pointer Up**:
    *   Commit changes via callbacks (`onUpdateFieldRange` or `onCreateField`).
    *   Reset state.

---

## 3. Boundary Algorithms

### Create Mode: `findGapBoundaries`
Expands outwards from the clicked bit to find the maximum contiguous empty region.

*   **Logic**:
    *   Walk `maxBit` up until `bits[maxBit + 1]` is not null or `registerSize` is reached.
    *   Walk `minBit` down until `bits[minBit - 1]` is not null or `0` is reached.

### Resize Mode: `findResizeBoundary`
Determines the hard limits for resizing a specific field.

*   **The "Range Redefine" Model**:
    *   When resizing, the user is NOT just moving one edge. They are defining a *new range* for the field using the drag selection.
    *   Therefore, the valid "sandbox" for the field is: `[Current Gap Below] + [Field Itself] + [Current Gap Above]`.
    *   **Lower Limit (`minBit`)**: The nearest collision with another field towards the LSB (or 0).
    *   **Upper Limit (`maxBit`)**: The nearest collision with another field towards the MSB (or 31).

---

## 4. Visual Feedback Logic

Visual feedback is computed dynamically during the render loop of the segments.

### The Selection Range
Defined mathematically as:
```typescript
const selectionLo = Math.min(shiftDrag.anchorBit, shiftDrag.currentBit);
const selectionHi = Math.max(shiftDrag.anchorBit, shiftDrag.currentBit);
```

### Gap Segment Rendering
When `mode === 'create'` OR `mode === 'resize'` (dragging field into gap):
*   **Active Bits**: Any bit `b` where `selectionLo <= b <= selectionHi`.
*   **Style**: Rendered with High Contrast Blue background and `+` symbol.

### Field Segment Rendering
When `mode === 'resize'`:
*   **Active Bits (`isInNewRange`)**: Bits inside the selection.
    *   **Style**: Solid opacity, Border highlight.
*   **Inactive Bits (`isOutOfNewRange`)**: Bits outside the selection (but inside the original field).
    *   **Concept**: These bits will be *discarded* if the user releases the mouse.
    *   **Style**: Low opacity (0.3), background color removed (grayed out).

---

## 5. Commit Logic

When the user releases the mouse:

**Mathematical Resolution**:
1.  Calculate final range `[H, L]` from `anchorBit` and `currentBit`.
2.  **If Resize**:
    *   Call `onUpdateFieldRange(targetIndex, [H, L])`.
    *   This atomic update overwrites the old range `[oldH, oldL]` with `[H, L]`.
    *   Any bits in `[oldH, oldL]` that are NOT in `[H, L]` become implicit gaps.
3.  **If Create**:
    *   Call `onCreateField({ bit_range: [H, L] })`.

This implementation ensures that "shrinking" a field is strictly equivalent to "selecting a sub-range" of that field, providing a predictable mental model for the user.
