-------------------------------
-- info_teleport_destination --
-------------------------------

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")

local InfoTeleportDestination = {}
InfoTeleportDestination.__index = InfoTeleportDestination
setmetatable(InfoTeleportDestination, {__index = GoldsrcEntity})

-- Spawnflags
InfoTeleportDestination.Flags = {
    NOT_IN_DEATHMATCH = 2048,  -- If enabled, this entity will not be present in multiplayer games.
}

------------------------------------
-- Constructor
------------------------------------

function InfoTeleportDestination:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), InfoTeleportDestination)

    -- Set facing angles (Pitch Yaw Roll)
    local pitch = (ent.angles and ent.angles[3]) or 0
    local yaw   = (ent.angles and ent.angles[2]) or 0
    local roll  = (ent.angles and ent.angles[1]) or 0

    obj.oFaceAnglePitch = degrees_to_sm64(pitch)
    obj.oFaceAngleYaw   = degrees_to_sm64(yaw)
    obj.oFaceAngleRoll  = degrees_to_sm64(roll)

    return self
end

------------------------------------
-- Registration
------------------------------------
GoldsrcEntity.register("info_teleport_destination", InfoTeleportDestination)

return InfoTeleportDestination
