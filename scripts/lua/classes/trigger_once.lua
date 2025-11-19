----------------------
-- trigger_multiple --
----------------------

local TriggerMultiple = require("trigger_multiple")

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

goldsrc_add_class("trigger_once", function(ent, obj)
    return TriggerOnce:new(ent, obj)
end)

return TriggerOnce