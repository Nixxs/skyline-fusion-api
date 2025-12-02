import math

def compute_hv_fov(diagonal_fov_deg, width_px, height_px):
    """
    Calculate horizontal and vertical FOV from diagonal FOV and image size.
    Parameters:
        diagonal_fov_deg (float): diagonal field of view in degrees
        width_px (int): image width in pixels
        height_px (int): image height in pixels
    Returns:
        (horizontal_fov_deg, vertical_fov_deg) in degrees
    """

    # Convert to radians
    theta_d = math.radians(diagonal_fov_deg)

    # Aspect ratio
    r = width_px / height_px

    # Helper value
    k = math.tan(theta_d / 2)

    # Horizontal FOV
    theta_h = 2 * math.atan((r * k) / math.sqrt(r**2 + 1))

    # Vertical FOV
    theta_v = 2 * math.atan(k / math.sqrt(r**2 + 1))
 
    # Convert back to degrees
    return math.degrees(theta_h), math.degrees(theta_v)
