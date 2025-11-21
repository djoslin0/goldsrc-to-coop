------------
-- cycler --
------------

local GoldsrcEntity = require("goldsrc_entity")

local Cycler = {}
Cycler.__index = Cycler
setmetatable(Cycler, {__index = GoldsrcEntity})

------------------------------------
-- Constructor
------------------------------------

function Cycler:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), Cycler)

    local yaw   = (ent.angles and ent.angles[2]) or 0
    local pitch = (ent.angles and ent.angles[1]) or 0

    obj.oFaceAnglePitch = degrees_to_sm64(pitch)
    obj.oFaceAngleYaw = degrees_to_sm64(yaw)

    if ent.model ~= nil and ent.model:sub(-4) == ".mdl" then
        local geo_name = ent.model:gsub("/", "_"):gsub("%.", "_") .. "_geo"
        local e_model_id = smlua_model_util_get_id(geo_name)
        obj_set_model_extended(obj, e_model_id)
    end

    return self
end

function Cycler:update()
end

------------------------------------
-- Registration
------------------------------------

goldsrc_add_class("cycler", function(ent, obj)
    return Cycler:new(ent, obj)
end)

return Cycler