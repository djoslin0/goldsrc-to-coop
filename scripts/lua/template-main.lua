-- name: Goldsrc Port - $LEVELNAME
-- description: Goldsrc Port - $LEVELNAME

hook_event(HOOK_ON_SYNC_VALID, function()
    if gNetworkPlayers[0].currLevelNum ~= LEVEL_$LEVELUNAME then
        warp_to_level(LEVEL_$LEVELUNAME, 1, 0)
    end
end)
