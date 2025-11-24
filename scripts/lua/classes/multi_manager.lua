-------------------
-- multi_manager --
-------------------

local GoldsrcEntity = require("goldsrc_entity")

local MultiManager = {}
MultiManager.__index = MultiManager
setmetatable(MultiManager, {__index = GoldsrcEntity})

local dt = 1/30

-- Spawnflags
MultiManager.Flags = {
    MULTITHREADED = 1 << 0,  -- 1
}

------------------------------------
-- Constructor
------------------------------------

function MultiManager:new(ent, obj)
    local self = setmetatable(GoldsrcEntity:new(ent, obj), MultiManager)

    self.multithreaded = GoldsrcEntity.has_flag(ent.spawnflags or 0, MultiManager.Flags.MULTITHREADED)
    self.targets = {}
    self.is_processing = false
    self.remaining_time = 0

    -- Collect targets and delays from keyvalues, handling # sign for multiple calls
    local known_keys = {
        classname = true,
        targetname = true,
        spawnflags = true,
        origin = true,
        angles = true,
        _aabb = true,
        -- Add other known keys if needed
    }

    for k, v in pairs(ent) do
        if not known_keys[k] and type(v) == "string" then
            local delay = tonumber(v)
            if delay then
                -- Strip # suffix to group multiple calls to the same target
                local base_target = k:gsub("#.*$", "")
                if not self.targets[base_target] then
                    self.targets[base_target] = {}
                end
                table.insert(self.targets[base_target], {delay = delay})
            end
        end
    end

    return self
end

function MultiManager:trigger(activator_entity_name)
    -- If not multithreaded and already processing, ignore new triggers
    if not self.multithreaded and self.is_processing then
        return
    end

    -- Fire all targets using goldsrc_fire_target with their respective delays
    local activator = activator_entity_name or self.ent.targetname
    local max_delay = 0
    for base_target, triggers in pairs(self.targets) do
        for _, trigger_info in ipairs(triggers) do
            local delay = trigger_info.delay
            goldsrc_fire_target(base_target, self.ent.targetname, activator, nil, nil, delay)
            if delay > max_delay then
                max_delay = delay
            end
        end
    end

    -- If not multithreaded, track processing time based on the longest delay
    if not self.multithreaded then
        self.is_processing = true
        self.remaining_time = max_delay
    end
end

function MultiManager:update()
    if self.is_processing then
        self.remaining_time = self.remaining_time - dt
        if self.remaining_time <= 0 then
            self.is_processing = false
            self.remaining_time = 0
        end
    end
end

------------------------------------
-- Registration
------------------------------------
GoldsrcEntity.register("multi_manager", MultiManager)

return MultiManager
