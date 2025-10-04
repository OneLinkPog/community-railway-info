-- Setup script for Railway Status Display
-- Downloads required files from Strawberry Foundations server

local function downloadFile(url, path)
    print("Downloading " .. path .. "...")
    local response = http.get(url)
    
    if response then
        local file = fs.open(path, "w")
        file.write(response.readAll())
        file.close()
        response.close()
        print("Successfully downloaded " .. path)
        return true
    else
        print("Failed to download " .. path)
        return false
    end
end

-- URLs for the required files
local files = {
    {
        url = "https://dl.strawberryfoundations.org/content/computercraft/railway_status/startup.lua",
        path = "/startup.lua"
    },
    {
        url = "https://dl.strawberryfoundations.org/content/computercraft/railway_status/config.lua",
        path = "/rinfo/config.lua"
    },
    {
        url = "https://dl.strawberryfoundations.org/content/computercraft/railway_status/displayutils.lua",
        path = "/rinfo/displayutils.lua"
    },
    {
        url = "https://dl.strawberryfoundations.org/content/computercraft/railway_status/theme.lua",
        path = "/rinfo/theme.lua"
    },
    {
        url = "https://dl.strawberryfoundations.org/content/computercraft/railway_status/json.lua",
        path = "/rinfo/json.lua"
    },
    {
        url = "https://dl.strawberryfoundations.org/content/computercraft/railway_status/client.lua",
        path = "/rinfo/client.lua"
    }
}

print("Railway Info Display Setup")
print("===========================")

-- Check if HTTP API is available
if not http then
    error("HTTP API is not enabled! Enable it in ComputerCraft config.")
end

-- Download all files
for _, file in ipairs(files) do
    downloadFile(file.url, file.path)
end

print("===========================")
print("Setup complete! Rebooting in 3 seconds...")
os.sleep(3)
os.reboot()