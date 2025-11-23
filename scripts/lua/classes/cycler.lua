------------
-- cycler --
------------

local GoldsrcEntity = require("goldsrc_entity")
local GoldsrcSpr = require("goldsrc_spr")

local Cycler = {}
Cycler.__index = Cycler
setmetatable(Cycler, {__index = GoldsrcEntity})

local dt = 1/30

------------------------------------
-- Constructor
------------------------------------

function Cycler:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), Cycler)

    local yaw   = (ent.angles and ent.angles[2]) or 0
    local pitch = (ent.angles and ent.angles[1]) or 0

    obj.oFaceAnglePitch = degrees_to_sm64(pitch)
    obj.oFaceAngleYaw   = degrees_to_sm64(yaw)

    local is_mdl = ent.model:sub(-4) == ".mdl"
    local is_spr = ent.model:sub(-4) == ".spr"

    self.spr = nil

    if ent.model ~= nil and (is_mdl or is_spr) then
        local geo_name = GoldsrcSpr.geo_path(ent.model)
        local e_model_id = smlua_model_util_get_id(geo_name)
        obj_set_model_extended(obj, e_model_id)

        if is_spr then
            self.spr = GoldsrcSpr:new(self)
        end
    end

    return self
end

function Cycler:update()
    if self.spr then
        self.spr:update()
    end
end

------------------------------------
-- Registration
------------------------------------
GoldsrcEntity.register("cycler", Cycler)

return Cycler