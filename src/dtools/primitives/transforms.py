from typing import TYPE_CHECKING, Literal

if TYPE_CHECKING:
    from dtools.workplane import Workplane

Alignment = Literal["start", "center", "end"]


def align(
    *workplanes: "Workplane",
    alignments: tuple[
        Alignment | None,
        Alignment | None,
        Alignment | None,
    ],
) -> tuple["Workplane", ...]:
    """
    Align multiple Workplanes based on the specified alignment type for each axis.

    Args:
        *workplanes: Variable number of Workplane objects to align
        alignments: Tuple of alignment types for (X, Y, Z) axes.
                   - "start": Align minimum bounding box values
                   - "center": Align centers of bounding boxes
                   - "end": Align maximum bounding box values
                   - None: No alignment on this axis

    Returns:
        Tuple of aligned Workplane objects (same length as input)

    Example:
        a, b, c = align(a, b, c, alignments=("center", None, None))
    """
    if not workplanes:
        return ()

    # Get bounding boxes for all workplanes
    bboxes = [wp.get_bbox() for wp in workplanes]

    # Calculate alignment targets for each axis
    targets = []
    for axis_idx, alignment in enumerate(alignments):
        if alignment is None:
            targets.append(None)
            continue

        if alignment == "start":
            # Find the smallest min value across all objects
            if axis_idx == 0:  # X axis
                target = min(bbox.xmin for bbox in bboxes)
            elif axis_idx == 1:  # Y axis
                target = min(bbox.ymin for bbox in bboxes)
            else:  # Z axis
                target = min(bbox.zmin for bbox in bboxes)
        elif alignment == "end":
            # Find the largest max value across all objects
            if axis_idx == 0:  # X axis
                target = max(bbox.xmax for bbox in bboxes)
            elif axis_idx == 1:  # Y axis
                target = max(bbox.ymax for bbox in bboxes)
            else:  # Z axis
                target = max(bbox.zmax for bbox in bboxes)
        elif alignment == "center":
            # Find the average center point
            if axis_idx == 0:  # X axis
                target = sum(bbox.center.x for bbox in bboxes) / len(bboxes)
            elif axis_idx == 1:  # Y axis
                target = sum(bbox.center.y for bbox in bboxes) / len(bboxes)
            else:  # Z axis
                target = sum(bbox.center.z for bbox in bboxes) / len(bboxes)
        else:
            target = None

        targets.append(target)

    # Apply transformations to each workplane
    result = []
    for wp, bbox in zip(workplanes, bboxes, strict=True):
        dx, dy, dz = 0.0, 0.0, 0.0

        # Calculate translation for X axis
        if targets[0] is not None:
            if alignments[0] == "start":
                dx = targets[0] - bbox.xmin
            elif alignments[0] == "end":
                dx = targets[0] - bbox.xmax
            elif alignments[0] == "center":
                dx = targets[0] - bbox.center.x

        # Calculate translation for Y axis
        if targets[1] is not None:
            if alignments[1] == "start":
                dy = targets[1] - bbox.ymin
            elif alignments[1] == "end":
                dy = targets[1] - bbox.ymax
            elif alignments[1] == "center":
                dy = targets[1] - bbox.center.y

        # Calculate translation for Z axis
        if targets[2] is not None:
            if alignments[2] == "start":
                dz = targets[2] - bbox.zmin
            elif alignments[2] == "end":
                dz = targets[2] - bbox.zmax
            elif alignments[2] == "center":
                dz = targets[2] - bbox.center.z

        # Apply translation using translate method
        aligned_wp = wp.translate((dx, dy, dz))
        result.append(aligned_wp)

    return tuple(result)


def move_center_to(workplane: "Workplane", loc: tuple[float, ...]) -> "Workplane":
    if not loc:
        return workplane

    bbox = workplane.get_bbox()
    current_x = (bbox.xmin + bbox.xmax) / 2
    current_y = (bbox.ymin + bbox.ymax) / 2
    current_z = (bbox.zmin + bbox.zmax) / 2

    dx, dy, dz = 0, 0, 0
    if len(loc) > 0:
        dx = loc[0] - current_x
    if len(loc) > 1:
        dy = loc[1] - current_y
    if len(loc) > 2:
        dz = loc[2] - current_z

    return workplane.translate((dx, dy, dz))
