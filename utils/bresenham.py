__all__ = ["bresenham"]

def bresenham(p0, p1):
    y0, x0 = p0
    y1, x1 = p1            

    swap_xy = abs(p1[0] - p0[0]) > abs(p1[1] - p0[1])

    if swap_xy:
        # Invert on swap_xy
        x0, y0 = p0
        x1, y1 = p1
        

    # Invert Direction
    swap_direction = x0 > x1
    if swap_direction:
        x1, x0 = (x0, x1)
        y1, y0 = (y0, y1)
            
    deltax = x1 - x0
    deltay = abs(y1 - y0)

    deltaerr = deltay / deltax
        
    ystep = -1
    if y0 < y1: ystep = 1
                
    x = x0
    y = y0
    error = 0
        
    points = []
        
    while x < x1:
        
        point = [int(y), int(x)]
        if swap_xy: point.reverse()
        points.append(tuple(point))
        
        error += deltaerr
        if error >= 0.5:
            y = y + ystep
            error -= 1.0
        x += 1
    
    
    if swap_direction: points.reverse()

    return iter(points)
