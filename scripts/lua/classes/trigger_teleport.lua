----------------------
-- trigger_teleport --
----------------------

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")

local TriggerTeleport = {}
TriggerTeleport.__index = TriggerTeleport
setmetatable(TriggerTeleport, {__index = GoldsrcEntity})

local sTeleporteeCooldowns = {}

local dt = 1/30

-------------------------------------------------
-- Constructor
-------------------------------------------------

function TriggerTeleport:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), TriggerTeleport)
    return self
end

function TriggerTeleport:teleport_entity(teleportee)
    local ent = self.ent

    if not ent.target then
        return
    end

    -- Check master (TODO: implement proper master logic)
    -- For now, assume no master or always active

    -- Find destination entities by name
    local destinations = goldsrc_get_entities_from_target_name(ent.target)
    local destination = #destinations > 0 and destinations[1]
    if not destination or not destination._class or not destination._class.obj then
        return  -- Destination not found
    end
    local dest_obj = destination._class.obj

    -- Teleport the player to destination position and orientation
    teleportee.pos.x = dest_obj.oPosX
    teleportee.pos.y = dest_obj.oPosY
    teleportee.pos.z = dest_obj.oPosZ

    teleportee.faceAngle.x = dest_obj.oFaceAnglePitch
    teleportee.faceAngle.y = dest_obj.oFaceAngleYaw + degrees_to_sm64(90)
    teleportee.faceAngle.z = dest_obj.oFaceAngleRoll

    -- Reset velocity to prevent carrying momentum
    teleportee.vel.x = 0
    teleportee.vel.y = 0
    teleportee.vel.z = 0
    teleportee.forwardVel = 0
end

function TriggerTeleport:update()
    local m = gMarioStates[0]

    -- Check if player is in the teleport area and cooldown is reset
    if goldsrc_intersects_aabb(m.pos, 80, self.ent._aabb) and (sTeleporteeCooldowns[m] or 0) <= 0 then
        self:teleport_entity(m)
        sTeleporteeCooldowns[m] = 1
    end

    sTeleporteeCooldowns[m] = math.max(0, (sTeleporteeCooldowns[m] or 0) - dt)
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("trigger_teleport", TriggerTeleport)

return TriggerTeleport
