----------------
-- func_water --
----------------

-- TODO: should we implement this fully? idk -- water works so different from goldsrc

local GoldsrcEntity = require("goldsrc_entity")

local FuncWater = {}
FuncWater.__index = FuncWater
setmetatable(FuncWater, {__index = GoldsrcEntity})

-------------------------------------------------
-- Constructor
-------------------------------------------------

function FuncWater:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), FuncWater)
    return self
end

-------------------------------------------------
-- Registration
-------------------------------------------------

GoldsrcEntity.register("func_water", FuncWater)

return FuncWater