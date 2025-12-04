local GoldsrcHull = {}

function GoldsrcHull.contains_point(point, hull)
    for _, plane in ipairs(hull.planes) do
        local n, d = plane.n, plane.d
        local dist = n[1]*point[1] + n[2]*point[2] + n[3]*point[3] - d
        if dist < 0 then
            -- outside this plane
            return false
        end
    end
    return true
end

function GoldsrcHull.within_radius(x, y, z, hull, radius)
    radius = radius or 0
    for _, plane in ipairs(hull.planes) do
        local n, d = plane.n, plane.d
        local dist = n[1]*x + n[2]*y + n[3]*z - d
        if dist < -radius then
            -- outside the hull by more than the radius
            return false
        end
    end
    return true
end

function GoldsrcHull.top_at(x, y, z, hull)
    local top_y = hull.max[2]  -- start with AABB top

    for _, plane in ipairs(hull.planes) do
        local n, d = plane.n, plane.d

        if math.abs(n[2]) > 0.01 then  -- any plane affecting Y
            local y_plane = (d - n[1]*x - n[3]*z) / n[2]
            if n[2] < 0 then
                -- normal pointing down -> constrains top
                if y_plane < top_y then
                    top_y = y_plane
                end
            end
        end
    end

    return top_y
end

return GoldsrcHull
