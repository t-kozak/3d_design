import re
import traceback
from enum import Enum
from pathlib import Path
from typing import Any, Tuple

import svgpathtools as svgt

from dtools.workplane import Workplane


class _PathType(Enum):
    """Type of SVG path to render."""

    FILLED = "filled"
    CLOSED_STROKE = "closed_stroke"
    OPEN_STROKE = "open_stroke"


def svg(
    wp: Workplane,
    svg: str | Path,
    height: float = 4,
    smooth: bool = True,
    x_len: float | None = None,
    y_len: float | None = None,
    center: bool = True,
    chamfer: float | None = None,
    chamfer_top: float | None = None,
    chamfer_bottom: float | None = None,
) -> Workplane:
    """
    Convert SVG elements to CadQuery wires for extrusion.

    Supports path, line, rect, circle, polygon, and ellipse SVG elements.

    Args:
        wp: Input workplane
        svg: SVG file path or SVG string content
        height: Extrusion height in mm
        smooth: If True, use bezier curves; if False, use linear segments
        x_len: Target width in mm (exactly one of x_len or y_len must be provided)
        y_len: Target height in mm (exactly one of x_len or y_len must be provided)
        center: If True, center shape at origin; if False, position at bottom-left
        chamfer: Optional chamfer size for both top and bottom edges
        chamfer_top: Optional chamfer size for top edges only (overrides chamfer)
        chamfer_bottom: Optional chamfer size for bottom edges only (overrides chamfer)

    Returns:
        Workplane with extruded SVG shapes

    Raises:
        ValueError: If both or neither of x_len/y_len are provided
    """
    # Validate dimensions
    if (x_len is None and y_len is None) or (x_len is not None and y_len is not None):
        raise ValueError("Exactly one of x_len or y_len must be provided")

    # Parse SVG and extract paths
    paths, attributes, svg_attrs = _load_svg(svg)

    if not paths:
        return wp

    # Calculate bounding box and scale
    bbox = _calculate_bounds(paths)
    svg_width = bbox[2] - bbox[0]
    svg_height = bbox[3] - bbox[1]
    scale = _calculate_scale(svg_width, svg_height, x_len, y_len)

    # Process each path individually
    solids = []
    for path, attrs in zip(paths, attributes, strict=True):
        # Inherit SVG-level attributes for paths that don't have their own
        merged_attrs = _merge_svg_attrs(attrs, svg_attrs)
        solid = _process_path(path, merged_attrs, bbox, scale, height, smooth, center)
        if solid is not None:
            solids.append(solid)

    if not solids:
        return wp

    # Determine actual chamfer values (specific overrides general)
    actual_chamfer_top = chamfer_top if chamfer_top is not None else chamfer
    actual_chamfer_bottom = chamfer_bottom if chamfer_bottom is not None else chamfer

    # Apply chamfer to individual solids before union (more robust)
    if actual_chamfer_top is not None or actual_chamfer_bottom is not None:
        processed_solids = []
        for i, solid in enumerate(solids):
            try:
                solid = _safe_chamfer(
                    solid, actual_chamfer_top, actual_chamfer_bottom, i
                )
                processed_solids.append(solid)
            except Exception as e:
                print(f"[solid {i}] Chamfer failed: {e}, using unchamfered solid")
                processed_solids.append(solid)
        solids = processed_solids

    # Combine all solids with union
    result = solids[0]
    for solid in solids[1:]:
        result = result.union(solid)

    return result


def _safe_chamfer(
    solid: Workplane,
    chamfer_top: float | None,
    chamfer_bottom: float | None,
    solid_id: int,
) -> Workplane:
    """
    Apply chamfer to top and/or bottom edges with multiple fallback strategies.

    Args:
        solid: Input workplane with solid
        chamfer_top: Chamfer size for top edges in mm (None to skip)
        chamfer_bottom: Chamfer size for bottom edges in mm (None to skip)
        solid_id: ID for debug output

    Returns:
        Chamfered workplane (or original if all strategies fail)
    """
    result = solid

    # Strategy 1: Try chamfering top and bottom edges separately
    try:
        if chamfer_top is not None:
            result = result.edges(">Z").chamfer(chamfer_top)
        if chamfer_bottom is not None:
            result = result.edges("<Z").chamfer(chamfer_bottom)
        return result
    except Exception:
        pass

    # Strategy 2: Try chamfering edges one at a time
    try:
        result = solid

        def make_edge_selector(target_edge):
            return lambda e: e.isSame(target_edge)

        if chamfer_top is not None:
            top_edges = solid.edges(">Z").vals()
            for edge in top_edges:
                try:
                    result = result.edges(make_edge_selector(edge)).chamfer(  # type: ignore
                        chamfer_top
                    )
                except Exception:
                    continue  # Skip problematic edges

        if chamfer_bottom is not None:
            bottom_edges = solid.edges("<Z").vals()
            for edge in bottom_edges:
                try:
                    result = result.edges(make_edge_selector(edge)).chamfer(  # type: ignore
                        chamfer_bottom
                    )
                except Exception:
                    continue  # Skip problematic edges

        return result
    except Exception:
        pass

    # Strategy 3: Try with smaller chamfer sizes
    try:
        result = solid
        if chamfer_top is not None:
            smaller_top = chamfer_top * 0.5
            result = result.edges(">Z").chamfer(smaller_top)
        if chamfer_bottom is not None:
            smaller_bottom = chamfer_bottom * 0.5
            result = result.edges("<Z").chamfer(smaller_bottom)
        return result
    except Exception:
        pass

    print(
        f"[solid {solid_id}] All chamfer strategies failed, returning unchamfered solid"
    )
    return solid


def _merge_svg_attrs(
    path_attrs: dict[str, Any], svg_attrs: dict[str, Any]
) -> dict[str, Any]:
    """
    Merge SVG-level attributes with path-level attributes.

    Path-level attributes take precedence over SVG-level attributes.
    This handles cases where fill/stroke are specified at the SVG element level.

    Args:
        path_attrs: Path-specific attributes
        svg_attrs: SVG element-level attributes

    Returns:
        Merged attributes dictionary
    """
    # Start with SVG-level attributes that matter for rendering
    relevant_svg_attrs = {}
    for key in ["fill", "stroke", "stroke-width"]:
        if key in svg_attrs:
            relevant_svg_attrs[key] = svg_attrs[key]

    # Override with path-level attributes (they take precedence)
    merged = {**relevant_svg_attrs, **path_attrs}
    return merged


def _parse_css_styles(svg_content: str) -> dict[str, dict[str, str]]:
    """
    Parse CSS styles from SVG <style> tags.

    Args:
        svg_content: Raw SVG content as string

    Returns:
        Dictionary mapping class names to style dictionaries
    """
    import xml.etree.ElementTree as ET

    styles = {}

    try:
        # Parse SVG to extract <style> content
        root = ET.fromstring(svg_content)

        # Find all <style> tags (handle namespaces)
        style_tags = root.findall(".//{http://www.w3.org/2000/svg}style")
        style_tags.extend(root.findall(".//style"))  # Try without namespace too

        for style_tag in style_tags:
            if style_tag.text:
                # Parse CSS rules (very simple parser for basic selectors)
                css_text = style_tag.text.strip()

                # Match rules like: .cls-1{fill:none;stroke:#020202;stroke-width:2px;}
                import re

                rule_pattern = r"\.([a-zA-Z0-9_-]+)\s*\{([^}]+)\}"
                for match in re.finditer(rule_pattern, css_text):
                    class_name = match.group(1)
                    properties = match.group(2)

                    # Parse properties
                    style_dict = {}
                    for prop in properties.split(";"):
                        prop = prop.strip()
                        if ":" in prop:
                            key, value = prop.split(":", 1)
                            style_dict[key.strip()] = value.strip()

                    styles[class_name] = style_dict

    except Exception:
        # If parsing fails, return empty dict
        pass

    return styles


def _resolve_attributes(
    attributes: dict[str, str], css_styles: dict[str, dict[str, Any]]
) -> dict[str, Any]:
    """
    Resolve element attributes by merging inline styles and CSS class styles.

    Args:
        attributes: Raw element attributes (may include 'class')
        css_styles: Parsed CSS styles from <style> tags

    Returns:
        Resolved attributes with CSS class styles applied
    """
    resolved = attributes.copy()

    # If element has a class, merge class styles
    if "class" in attributes:
        class_name = attributes["class"]
        if class_name in css_styles:
            # Apply class styles (inline attributes take precedence)
            for key, value in css_styles[class_name].items():
                if key not in resolved:
                    resolved[key] = value

    return resolved


def _load_svg(
    svg: str | Path,
) -> Tuple[list[svgt.Path], list[dict[str, Any]], dict[str, str]]:
    """
    Load SVG and extract paths with their attributes.

    Args:
        svg: Path to SVG file or SVG string content

    Returns:
        Tuple of (paths, attributes, svg_attributes)
    """
    # Read SVG content for CSS parsing
    if isinstance(svg, Path) or (isinstance(svg, str) and Path(svg).exists()):
        # It's a file path
        with open(svg) as f:
            svg_content = f.read()
        fn = svgt.svg2paths
        fn_arg = str(svg)
    else:
        # It's an SVG string
        svg_content = svg
        fn = svgt.svgstr2paths
        fn_arg = svg

    # Parse CSS styles from <style> tags
    css_styles = _parse_css_styles(svg_content)

    res = fn(
        fn_arg,
        return_svg_attributes=True,
        convert_circles_to_paths=True,
        convert_ellipses_to_paths=True,
        convert_lines_to_paths=True,
        convert_polylines_to_paths=True,
        convert_polygons_to_paths=True,
        convert_rectangles_to_paths=True,
    )
    paths: list[svgt.Path] = res[0]
    attributes = res[1]
    svg_attrs = res[2] if len(res) > 2 else {}

    # Resolve CSS class styles for each element
    resolved_attributes = [
        _resolve_attributes(attrs, css_styles) for attrs in attributes
    ]

    return paths, resolved_attributes, svg_attrs


def _calculate_bounds(paths: list[svgt.Path]) -> Tuple[float, float, float, float]:
    """
    Calculate overall bounding box for all paths.

    Args:
        paths: List of svgpathtools Path objects

    Returns:
        Tuple of (xmin, ymin, xmax, ymax)
    """
    if not paths:
        return (0, 0, 0, 0)

    # Get bbox for first path
    xmin, xmax, ymin, ymax = paths[0].bbox()

    # Expand to include all other paths
    for path in paths[1:]:
        px_min, px_max, py_min, py_max = path.bbox()
        xmin = min(xmin, px_min)
        xmax = max(xmax, px_max)
        ymin = min(ymin, py_min)
        ymax = max(ymax, py_max)

    return (xmin, ymin, xmax, ymax)


def _calculate_scale(
    svg_width: float, svg_height: float, x_len: float | None, y_len: float | None
) -> float:
    """
    Calculate uniform scale factor based on target dimensions.

    Args:
        svg_width: Width of SVG in SVG units
        svg_height: Height of SVG in SVG units
        x_len: Target width in mm (or None)
        y_len: Target height in mm (or None)

    Returns:
        Uniform scale factor
    """
    if x_len is not None:
        return x_len / svg_width
    elif y_len is not None:
        return y_len / svg_height
    else:
        # Should never reach here due to validation in main function
        raise ValueError("Either x_len or y_len must be provided")


def _transform_point(
    x: float,
    y: float,
    bbox: Tuple[float, float, float, float],
    scale: float,
    center: bool,
) -> Tuple[float, float]:
    """
    Transform SVG coordinates to CadQuery coordinates.

    Args:
        x: X coordinate in SVG space
        y: Y coordinate in SVG space
        bbox: Bounding box (xmin, ymin, xmax, ymax)
        scale: Scale factor
        center: Whether to center the result

    Returns:
        Tuple of (x_cq, y_cq) in CadQuery space
    """
    xmin, ymin, xmax, ymax = bbox

    # Flip Y-axis (SVG has Y pointing down, CadQuery has Y pointing up)
    y_flipped = (ymax + ymin) - y

    # Apply scale
    x_scaled = x * scale
    y_scaled = y_flipped * scale

    # Apply centering or corner positioning
    if center:
        x_final = x_scaled - ((xmax - xmin) * scale / 2)
        y_final = y_scaled - ((ymax - ymin) * scale / 2)
    else:
        x_final = x_scaled - (xmin * scale)
        y_final = y_scaled - (ymin * scale)

    return (x_final, y_final)


def _has_fill(attributes: dict[str, Any]) -> bool:
    """
    Check if path has a fill attribute.

    Args:
        attributes: SVG attributes dictionary

    Returns:
        True if path should be filled
    """
    fill = attributes.get("fill", "")
    stroke = attributes.get("stroke", "")

    # If fill is explicitly "none", it's not filled
    if fill == "none":
        return False

    # If there's an explicit fill value (not empty), it's filled
    if fill and fill != "":
        return True

    # If there's no fill but there's a stroke, it's stroke-only
    if stroke and stroke != "none" and stroke != "":
        return False

    # Default SVG behavior: if nothing is specified, paths are filled with black
    # But if stroke is specified without fill, treat as stroke-only
    return fill != ""


def _extract_stroke_width(attributes: dict[str, Any], scale: float) -> float:
    """
    Extract and scale stroke width from SVG attributes.

    The stroke width is parsed from the SVG attributes and converted to mm
    using the same scale factor that converts SVG coordinates to physical space.
    This ensures stroke widths scale proportionally with the overall SVG size.

    Args:
        attributes: SVG attributes dictionary
        scale: Scale factor (mm per SVG unit) calculated from bbox and x_len/y_len

    Returns:
        Stroke width in mm
    """
    stroke = attributes.get("stroke", "none")
    if stroke == "none" or stroke == "":
        return 1.0  # Default stroke width in mm

    stroke_width_str = attributes.get("stroke-width", "1")

    # Parse numeric value (handle units)
    match = re.match(r"([0-9.]+)(px|mm|pt|in)?", str(stroke_width_str))
    if match:
        value = float(match.group(1))
        unit = match.group(2) or "px"

        # For px (or no unit): the value is in SVG coordinate space
        # Apply the scale factor to convert to mm
        if unit == "px" or unit is None:
            return value * scale

        # For absolute units, convert directly to mm
        # (these don't scale with the SVG - they're absolute physical sizes)
        if unit == "mm":
            return value
        elif unit == "pt":
            return value * 0.352778  # pt to mm: 1pt = 1/72 inch, 1 inch = 25.4mm
        elif unit == "in":
            return value * 25.4  # inches to mm

    return 1.0


def _determine_path_type(path: svgt.Path, attributes: dict[str, Any]) -> _PathType:
    """
    Determine the type of path based on SVG attributes and path properties.

    Args:
        path: svgpathtools Path object
        attributes: SVG attributes dictionary

    Returns:
        PathType enum indicating how to render this path
    """
    has_fill = _has_fill(attributes)

    # Try to check if path is closed
    # Some paths (with discontinuous segments) will raise AssertionError
    is_closed = False
    try:
        is_closed = path.isclosed()
    except AssertionError:
        # Path is not continuous, so it can't be checked with isclosed()
        # Discontinuous paths are typically filled paths
        pass

    # Check if first and last points are the same
    first_last_match = False
    if len(path) > 0:
        first_point = path[0].start
        last_point = path[-1].end
        # Compare with a small tolerance for floating point errors
        first_last_match = abs(first_point - last_point) < 1e-6

    if has_fill:
        return _PathType.FILLED
    elif is_closed:
        return _PathType.CLOSED_STROKE
    elif first_last_match:
        return _PathType.CLOSED_STROKE
    else:
        return _PathType.OPEN_STROKE


def _split_discontinuous_path(path: svgt.Path) -> list[svgt.Path]:
    """
    Split a discontinuous path into multiple continuous sub-paths.

    Args:
        path: svgpathtools Path object (may be discontinuous)

    Returns:
        List of continuous Path objects
    """
    if len(path) == 0:
        return []

    # Check if path is continuous
    try:
        if path.iscontinuous():
            return [path]
    except AssertionError:
        pass  # Path is discontinuous, proceed with splitting

    # Split at discontinuities
    sub_paths = []
    current_segments = []

    for i, segment in enumerate(path):
        if i > 0:
            # Check if this segment connects to the previous one
            prev_end = path[i - 1].end
            curr_start = segment.start
            if abs(prev_end - curr_start) > 1e-6:
                # Discontinuity found - save current sub-path
                if current_segments:
                    sub_paths.append(svgt.Path(*current_segments))
                current_segments = []

        current_segments.append(segment)

    # Add final sub-path
    if current_segments:
        sub_paths.append(svgt.Path(*current_segments))

    return sub_paths


def _path_to_wire(
    path: svgt.Path,
    bbox: Tuple[float, float, float, float],
    scale: float,
    smooth: bool,
    center: bool,
):
    """
    Convert svgpathtools Path to CadQuery wire.

    Args:
        path: svgpathtools Path object
        bbox: Bounding box for transformation
        scale: Scale factor
        smooth: Whether to use smooth curves
        center: Whether to center the result

    Returns:
        CadQuery workplane with wire
    """
    from dtools.workplane import Workplane

    if len(path) == 0:
        return None

    # Start with a fresh workplane
    temp_wp = Workplane("XY")

    # Get first point
    first_point = path[0].start
    start_x, start_y = _transform_point(
        first_point.real, first_point.imag, bbox, scale, center
    )
    temp_wp = temp_wp.moveTo(start_x, start_y)

    # Process each segment
    for segment in path:
        if isinstance(segment, svgt.Line):
            # Line segment
            end = segment.end
            end_x, end_y = _transform_point(end.real, end.imag, bbox, scale, center)
            temp_wp = temp_wp.lineTo(end_x, end_y)

        elif isinstance(segment, (svgt.QuadraticBezier, svgt.CubicBezier)):
            # Bezier curve
            if smooth:
                # Use bezier curve
                points = []
                if isinstance(segment, svgt.QuadraticBezier):
                    # Quadratic: start, control, end
                    for pt in [segment.start, segment.control, segment.end]:
                        x, y = _transform_point(pt.real, pt.imag, bbox, scale, center)
                        points.append((x, y))
                else:
                    # Cubic: start, control1, control2, end
                    for pt in [
                        segment.start,
                        segment.control1,
                        segment.control2,
                        segment.end,
                    ]:
                        x, y = _transform_point(pt.real, pt.imag, bbox, scale, center)
                        points.append((x, y))

                temp_wp = temp_wp.bezier(points)
            else:
                # Sample curve with line segments
                num_samples = 10
                for i in range(1, num_samples + 1):
                    t = i / num_samples
                    pt = segment.point(t)
                    x, y = _transform_point(pt.real, pt.imag, bbox, scale, center)
                    temp_wp = temp_wp.lineTo(x, y)

        elif isinstance(segment, svgt.Arc):
            # Arc segment - sample intermediate point
            mid_point = segment.point(0.5)
            end_point = segment.end

            mid_x, mid_y = _transform_point(
                mid_point.real, mid_point.imag, bbox, scale, center
            )
            end_x, end_y = _transform_point(
                end_point.real, end_point.imag, bbox, scale, center
            )

            temp_wp = temp_wp.threePointArc((mid_x, mid_y), (end_x, end_y))

    return temp_wp


def _process_filled_path(
    wire_wp: Workplane,
    height: float,
) -> Workplane:
    """
    Process a filled path by extruding it to create a solid body.

    Args:
        wire_wp: Workplane containing the wire to extrude
        height: Extrusion height in mm

    Returns:
        Workplane with extruded solid
    """
    return wire_wp.close().extrude(height)


def _process_closed_stroke_path(
    wire_wp: Workplane,
    height: float,
    stroke_width: float,
) -> Workplane:
    """
    Process a closed stroke path by creating a hollow shell.

    Args:
        wire_wp: Workplane containing the closed wire
        height: Extrusion height in mm
        stroke_width: Thickness of the stroke in mm

    Returns:
        Workplane with hollow extruded solid
    """
    # Extrude as solid, then shell to create hollow wire
    solid = wire_wp.close().extrude(height)
    # Shell the top and bottom faces to hollow it out
    # Negative value shells inward, creating wall thickness
    # return solid
    return solid.faces(">Z or <Z").shell(stroke_width)


def _process_open_stroke_path(
    wire_wp: Workplane,
    height: float,
    stroke_width: float,
) -> Workplane:
    """
    Process an open stroke path by offsetting and shelling.

    Args:
        wire_wp: Workplane containing the open wire
        height: Extrusion height in mm
        stroke_width: Thickness of the stroke in mm

    Returns:
        Workplane with extruded stroke
    """
    # Close it first using offset2D, then use shell
    wire_wp = wire_wp.close().offset2D(stroke_width / 2)
    solid = wire_wp.extrude(height)
    return solid


def _process_path(
    path: svgt.Path,
    attrs: dict[str, Any],
    bbox: Tuple[float, float, float, float],
    scale: float,
    height: float,
    smooth: bool,
    center: bool,
) -> Workplane | None:
    """
    Process a single SVG path and convert it to a CadQuery solid.

    Args:
        path: svgpathtools Path object
        attrs: SVG attributes for this path
        bbox: Bounding box for transformation
        scale: Scale factor
        height: Extrusion height in mm
        smooth: Whether to use smooth curves
        center: Whether to center the result

    Returns:
        Workplane with processed solid, or None if processing failed
    """
    # Get element ID for debugging
    element_id = attrs.get("id", "unknown")

    # Determine path type first
    path_type = _determine_path_type(path, attrs)
    stroke_width = _extract_stroke_width(attrs, scale)

    # Debug output - safely check if closed
    try:
        is_closed = path.isclosed()
        is_continuous = True
    except AssertionError:
        is_closed = "N/A (discontinuous)"
        is_continuous = False

    print(
        f"[{element_id}] closed={is_closed}, continuous={is_continuous}, "
        f"type={path_type.value}, stroke_width={stroke_width:.2f}"
    )

    # Handle discontinuous paths by splitting them
    if not is_continuous:
        sub_paths = _split_discontinuous_path(path)
        print(f"[{element_id}] Split into {len(sub_paths)} sub-paths")

        # Process each sub-path and union them
        solids = []
        for i, sub_path in enumerate(sub_paths):
            sub_attrs = attrs.copy()
            sub_attrs["id"] = f"{element_id}_sub{i}"
            solid = _process_path(
                sub_path, sub_attrs, bbox, scale, height, smooth, center
            )
            if solid is not None:
                solids.append(solid)

        if not solids:
            return None

        # Union all sub-path solids
        result = solids[0]
        for solid in solids[1:]:
            result = result.union(solid)
        return result

    # Convert path to wire (for continuous paths only)
    wire_wp = _path_to_wire(path, bbox, scale, smooth, center)

    if wire_wp is None:
        print(f"[{element_id}] Skipping: wire_wp is None")
        return None

    # Create solid based on path type
    try:
        if path_type == _PathType.FILLED:
            solid = _process_filled_path(wire_wp, height)
        elif path_type == _PathType.CLOSED_STROKE:
            solid = _process_closed_stroke_path(wire_wp, height, stroke_width)
        else:  # PathType.OPEN_STROKE
            solid = _process_open_stroke_path(wire_wp, height, stroke_width)

        print(f"[{element_id}] Successfully created solid")
        return solid

    except Exception:
        # Skip paths that can't be extruded
        print(f"[{element_id}] ERROR:")
        print(traceback.format_exc())
        return None


if __name__ == "__main__":
    import sys

    from ocp_vscode import show

    if len(sys.argv) < 2:
        print("Usage: python -m dtools.svg <svg_path> [options]")
        print("Options:")
        print("  x_len=<value>          - Scale to width in mm")
        print("  y_len=<value>          - Scale to height in mm")
        print("  chamfer=<value>        - Chamfer both top and bottom edges")
        print("  chamfer_top=<value>    - Chamfer top edges only")
        print("  chamfer_bottom=<value> - Chamfer bottom edges only")
        print("  height=<value>         - Extrusion height (default: 4)")
        print("\nExamples:")
        print("  python -m dtools.svg images/turnip.svg x_len=100")
        print("  python -m dtools.svg images/turnip.svg x_len=100 chamfer=0.5")
        print("  python -m dtools.svg images/turnip.svg x_len=100 chamfer_top=0.8")
        print(
            "  python -m dtools.svg images/turnip.svg y_len=50 "
            "chamfer_bottom=0.3 height=10"
        )
        sys.exit(1)

    svg_path = Path(sys.argv[1])

    # Parse optional arguments
    x_len = None
    y_len = None
    chamfer_val = None
    chamfer_top_val = None
    chamfer_bottom_val = None
    height_val = 4

    for arg in sys.argv[2:]:
        if "=" in arg:
            key, value = arg.split("=", 1)
            if key == "x_len":
                x_len = float(value)
            elif key == "y_len":
                y_len = float(value)
            elif key == "chamfer":
                chamfer_val = float(value)
            elif key == "chamfer_top":
                chamfer_top_val = float(value)
            elif key == "chamfer_bottom":
                chamfer_bottom_val = float(value)
            elif key == "height":
                height_val = float(value)

    # Default to x_len=100 if no dimension specified
    if x_len is None and y_len is None:
        x_len = 100

    sample = svg(
        Workplane("XY"),
        svg_path,
        x_len=x_len,
        y_len=y_len,
        height=height_val,
        chamfer=chamfer_val,
        chamfer_top=chamfer_top_val,
        chamfer_bottom=chamfer_bottom_val,
    )
    show(sample)
