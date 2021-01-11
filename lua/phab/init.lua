local function get_path()
	return vim.g.phab_path:match("^(.+)/.+$"):match("^(.+)/.+$")
end

local function get_file_path()
	local file_reg = vim.api.nvim_eval('@%')
	return file_reg
end

local function get_file_folder()
	return get_file_path():match("^(.+)/.+$")
end

local function get_task_id()
	local file_reg = get_file_path()
	name = file_reg:match("^.+/(.+)%..+$")
	return name
end

local function tasks_command(command, task, args)
	return vim.fn.system("python3 " .. get_path() .. "/py/task.py " .. command .. " " .. task .. " " .. args)
end

local function update_task()
	tasks_command("update", get_task_id(), get_file_path())
end

local function sync_task()
	tasks_command("sync", get_task_id(), get_file_path())
end

local function create_task()
	local title = vim.fn.input("Task Title > ")
	local output = tasks_command("create", "Txxx", string.format("\"%s\"", title))
	local path = string.format("%s/%s", get_file_folder(), output)
	vim.api.nvim_command("edit " .. path)
end

return {
	update_task = update_task,
	sync_task = sync_task,
	create_task = create_task,
	get_path = get_path
}

