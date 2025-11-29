----------------------
-- trigger_multiple --
----------------------

local GoldsrcEntity = require("/goldsrc/goldsrc_entity")
local TriggerMultiple = require("/goldsrc/trigger_multiple")

local TriggerOnce = {}
TriggerOnce.__index = TriggerOnce
setmetatable(TriggerOnce, {__index = TriggerMultiple})

------------------------------------
-- Constructor
------------------------------------

function TriggerOnce:new(ent, obj)
    local self = setmetatable(TriggerMultiple:new(ent, obj), TriggerOnce)
    ent.wait = -1
    return self
end

------------------------------------
-- Registration
------------------------------------
GoldsrcEntity.register("trigger_once", TriggerOnce)

return TriggerOnce