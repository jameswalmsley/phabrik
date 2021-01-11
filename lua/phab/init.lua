local function get_path()
	return vim.g.phab_path:match("^(.+)/.+$"):match("^(.+)/.+$")
end

local function get_file_path()
	local file_reg = vim.api.nvim_eval('@%')
	return file_reg
end

local function get_task_id()
	local file_reg = get_file_path()
	name = file_reg:match("^.+/(.+)%..+$")
	return name
end

local function tasks_command(command, task, args)
	vim.api.nvim_command("!python3 " .. get_path() .. "/py/task.py " .. command .. " " .. task .. " " .. args)
end

local function update_task()
	tasks_command("description", get_task_id(), get_file_path())
end

local function update_points()

	points = vim.fn.input("How many points? > ")
	tasks_command("points", get_task_id(), points)
end

return {
	update_task = update_task,
	update_points = update_points,
	get_path = get_path
}

