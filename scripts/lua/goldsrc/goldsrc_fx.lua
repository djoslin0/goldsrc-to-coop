local GoldsrcFx = {}

function GoldsrcFx.spawn_triangle_break_particles(obj, numTris, triModel, triSize, triAnimState)
    for i = 1, numTris do
        local triangle = spawn_non_sync_object(id_bhvBreakBoxTriangle, triModel, obj.oPosX, obj.oPosY, obj.oPosZ, nil)
        if triangle == nil then
            goto continue
        end

        triangle.oAnimState = triAnimState
        triangle.oPosY = triangle.oPosY + 100.0
        triangle.oMoveAngleYaw = random_u16()
        triangle.oFaceAngleYaw = triangle.oMoveAngleYaw
        triangle.oFaceAnglePitch = random_u16()
        triangle.oVelY = random_f32_around_zero(50.0)

        if triModel == 138 or triModel == 56 then
            triangle.oAngleVelPitch = 0xF00
            triangle.oAngleVelYaw = 0x500
            triangle.oForwardVel = 30.0
        else
            triangle.oAngleVelPitch = 0x80 * (math.floor(random_float() + 50.0))
            triangle.oForwardVel = 30.0
        end

        obj_scale(triangle, triSize)

        ::continue::
    end
end

return GoldsrcFx