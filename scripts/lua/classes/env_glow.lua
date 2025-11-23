--------------
-- env_glow --
--------------

local GoldsrcEntity = require("goldsrc_entity")
local GoldsrcSpr = require("goldsrc_spr")

local EnvGlow = {}
EnvGlow.__index = EnvGlow
setmetatable(EnvGlow, {__index = GoldsrcEntity})

------------------------------------
-- Constructor
------------------------------------

function EnvGlow:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), EnvGlow)

    local is_spr = ent.model:sub(-4) == ".spr"
    self.spr = nil

    if ent.model ~= nil and is_spr then
        local geo_name = GoldsrcSpr.geo_path(ent.model)
        local e_model_id = smlua_model_util_get_id(geo_name)
        obj_set_model_extended(obj, e_model_id)
        self.spr = GoldsrcSpr:new(self)
    end

    return self
end

function EnvGlow:update()
end

------------------------------------
-- Registration
------------------------------------
GoldsrcEntity.register("env_glow", EnvGlow)

return EnvGlow