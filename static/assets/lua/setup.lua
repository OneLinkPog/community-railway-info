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
        url = "https://dl.strawberryfoundations.org/content/computercraft/railway_status/display.lua",
        path = "/display.lua"
    }
}

print("Railway Status Display Setup")
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