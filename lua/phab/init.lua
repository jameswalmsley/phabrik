local function get_path()
	return vim.g.phab_path:match("^(.+)/.+$"):match("^(.+)/.+$")
end

local function update_task()
	local path = get_path()
	local file_reg = vim.api.nvim_eval('@%')
	name = file_reg:match("^.+/(.+)%..+$")

	vim.api.nvim_command("!python3 " .. path .. "/py/task.py " .. "T" .. name .. " " .. file_reg)
end


return {
	update_task = update_task,
	get_path = get_path
}

