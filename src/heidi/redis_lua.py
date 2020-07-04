class RedisLUA:
    def __init__(self, source):
        self.source = source
        self.digest = None

    async def eval(self, redis, keys=[], args=[]):
        if self.digest is None:
            self.digest = await redis.script_load(self.source)
        return await redis.evalsha(self.digest, keys=keys, args=args)


update_delivery_status = RedisLUA('''
--[[
    #ARGV == 1 means 'courier did his best, but there
    is no one to deliver to in the given domain'.
--]]

if #ARGV == 1 then
    local chan = string.format('__keyspace@0__:%s', KEYS[1])
    redis.call('PUBLISH', chan, 'set')
    return 1
end

local history = cjson.decode(redis.call('GET', KEYS[1]))
local provider = ARGV[1]

--[[
    history['recipients'] and ARGV[1:] MUST be sorted in ascending order.
--]]

local argv_iter = 2
for i = 1, #history['recipients'], 1 do
    if argv_iter > #ARGV then
        break
    end

    local user = history['recipients'][i]
    if user['id'] == tonumber(ARGV[argv_iter]) then
        local received_in = user['received_in']
        received_in[#received_in + 1] = provider

        history['recipients'][i]['received_in'] = received_in

        argv_iter = argv_iter + 1
    end
end

--[[
    Redis built-in `cjson` converts empty arrays to objects and doesn't
    seem to provide any solution for this issue.

    TODO: https://github.com/openresty/lua-cjson
--]]

local result = cjson.encode(history)

result = string.gsub(result, '\"origin\":{}', '\"origin\":[]')
result = string.gsub(result, '\"received_in\":{}', '\"received_in\":[]')

redis.call('SET', KEYS[1], result)
return 1
''')
