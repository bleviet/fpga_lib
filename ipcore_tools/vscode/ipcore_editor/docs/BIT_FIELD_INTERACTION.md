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

---

## 6. Visual Resize Handles

When the user holds the **Shift** key while hovering over a field, arrow indicators appear on resizable edges.

### Edge Detection (`getResizableEdges`)

For each field, we compute resize capabilities per edge:

```typescript
function getResizableEdges(fieldStart, fieldEnd, bitOwners, registerSize) {
  const msbBit = Math.max(fieldStart, fieldEnd);
  const lsbBit = Math.min(fieldStart, fieldEnd);
  const fieldWidth = msbBit - lsbBit + 1;

  const canShrink = fieldWidth > 1;
  const hasGapLeft = lsbBit > 0 && bitOwners[lsbBit - 1] === null;
  const hasGapRight = msbBit < registerSize - 1 && bitOwners[msbBit + 1] === null;

  return {
    left: { canShrink, canExpand: hasGapLeft },
    right: { canShrink, canExpand: hasGapRight },
  };
}
```

### Visual-to-Logical Mapping

Due to MSB-first rendering (higher bits on the left):
- **Visual left** = MSB edge (`edges.right`)
- **Visual right** = LSB edge (`edges.left`)

### Arrow Types

| Condition | Arrow | Meaning |
|-----------|-------|---------|
| `canShrink && canExpand` | ↔ (bidirectional) | Can shrink inward OR expand into gap |
| `canExpand` only | ← or → (outward) | Single-bit field, can only expand |
| `canShrink` only | → or ← (inward) | Multi-bit field at register boundary, can only shrink |

### Anchor Determination

When the user clicks to start a resize, the **opposite edge** becomes the anchor (fixed point):

```typescript
const fieldMid = (fieldRange.lo + fieldRange.hi) / 2;
const grabbingMsbEdge = bit >= fieldMid;
const anchorBit = grabbingMsbEdge ? fieldRange.lo : fieldRange.hi;
```

This ensures intuitive drag behavior: dragging from bit 31 toward 16 on field [31:1] yields [16:1], not [31:16].

---

# Ctrl-Drag Bit Field Interaction: Reordering Implementation

The "Ctrl-Drag" feature allows users to reorder fields and split gaps by treating the register as a list of movable segments.

## 1. The Reorder Model

Unlike Shift-Drag which modifies ranges in place, Ctrl-Drag treats the register as a collection of "Blocks" (Fields) and "Spacers" (Gaps).

### Key Concepts
*   **Gap Mutability**: Gaps are "first-class citizens" in the layout list but are *mutable*. They can be split, shrunk, or merged to accommodate field movements.
*   **Conservation of Width**: Moving a field preserves its bit-width. The field is essentially "lifted" from the layout and "dropped" into a new location, pushing other elements aside (or splitting them).
*   **Implicit Repacking**: The final bit positions of ALL fields are recalculated from LSB (0) upwards based on the new order of segments.

---

## 2. Reorder Algorithm (`handleCtrlPointerMove`)

The core logic executes on every pointer move event to generate a live preview.

### Step 1: Segmentation & Cleaning
1.  **Generate Segments**: Call `buildProLayoutSegments` to get the current state `[S_n, ..., S_0]` (MSB to LSB).
2.  **Extract Dragged Field**: Identify the field being dragged (`F_drag`).
3.  **Remove & Merge**: Remove `F_drag` from the list. 
    *   *Implicit Gap Creation*: Removing `F_drag` leaves a logical "hole".
    *   *Simplification*: The algorithm works on a "Clean List" of remaining segments. Since we repack from LSB=0 later, any "hole" left by the dragged field naturally closes up if we don't insert a spacer.
    *   *Wait*: Actually, the algorithm *keeps* the remaining segments in their relative order but repacks them tightly to create a coordinate space for the cursor.

### Step 2: Hitting the Target
1.  **Coordinate Space**: The "Clean List" is conceptually repacked from 0. This defines a mapping from `0..31` to `Segment Index`.
2.  **Cursor Mapping**: The user's cursor bit `B` is mapped against this packed namespace.
    *   `Target Segment T` is found such that `T.start <= B <= T.end`.

### Step 3: Insertion & Splitting
Once the Target `T` is identified, we insert `F_drag` relative to it.

#### Case A: Target is a Field
*   **Split Logic**: We cannot split a field. We insert *Before* or *After*.
*   **Decision**: Check if cursor `B` is in the upper half or lower half of `T`.
    *   Upper Half: Insert `F_drag` on the MSB side of `T`.
    *   Lower Half: Insert `F_drag` on the LSB side of `T`.

#### Case B: Target is a Gap
*   **Split Logic**: A Gap can be split into `[Gap_Top] [F_drag] [Gap_Bot]`.
*   **Calculation**:
    *   `Offset = B - T.start` (Local offset in gap).
    *   `Gap_Bot` width = `Offset`.
    *   `Gap_Top` width = `T.width - Offset`.
    *   If `Offset == 0`, `Gap_Bot` is empty (dropped).
    *   If `Offset == T.width`, `Gap_Top` is empty (dropped).

### Step 4: Final Repacking
1.  Construct the new list: `[...Segments_Above, (Gap_Top), F_drag, (Gap_Bot), ...Segments_Below]`.
2.  **Repack Loop**: Iterate from LSB (end of reverse list).
    *   `Current_Bit = 0`.
    *   For each segment:
        *   `Seg.start = Current_Bit`.
        *   `Seg.end = Current_Bit + Seg.width - 1`.
        *   `Current_Bit += Seg.width`.
3.  **Result**: A list of `previewSegments` with fully resolved bit ranges.

---

## 3. Atomic Commit Mechanism

Since a reorder operation can change the bit ranges of *multiple* fields simultaneously (e.g., swapping two fields changes valid bits for both), updates must be atomic.

### The Problem: Race Conditions
If `onUpdateFieldRange` is called sequentially for multiple fields:
1.  Update Field A -> Triggers Parent State Update.
2.  Update Field B -> Triggers Parent State Update (using stale state from before Step 1).
3.  Result: Step 1 is lost.

### The Solution: `onBatchUpdateFields`
We introduced a specific callback props for batch operations.

```typescript
onBatchUpdateFields: (updates: { idx: number; range: [number, number] }[]) => void
```

**Implementation in `DetailsPanel`**:
1.  Clone `fields` array.
2.  Apply all updates locally to the clone.
3.  **Sort**: Re-sort the array by LSB to ensure logical table order.
4.  **Single Commit**: Call `onUpdate(['fields'], newFields)` once.
