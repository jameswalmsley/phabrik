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

local function phab_command(command, task, args)
	return vim.fn.system("python3 " .. get_path() .. "/py/phab.py " .. command .. " " .. task .. " " .. args)
end

local function phab_commandlist(command, task, args)
	return vim.fn.systemlist("python3 " .. get_path() .. "/py/phab.py " .. command .. " " .. task .. " " .. args)
end

local function update_task()
	phab_command("update", get_task_id(), get_file_path())
end

local function sync_task()
	phab_command("sync", get_task_id(), get_file_path())
end

local function create_task()
	local title = vim.fn.input("Task Title > ")
	local output = phab_command("create", "Txxx", string.format("\"%s\"", title))
	local path = string.format("%s/%s", get_file_folder(), output)
	vim.api.nvim_command("edit " .. path)
end

local api = vim.api

local function get_diff()
	local diffnum = vim.fn.expand('<cWORD>')

	local buf = api.nvim_create_buf(true, true) -- create new emtpy buffer
	--api.nvim_buf_set_option(buf, 'bufhidden', 'wipe')
	api.nvim_buf_set_var(buf, 'diff-num', diffnum)


	local diff = phab_commandlist("diff", diffnum, "test")
	api.nvim_buf_set_lines(buf, 0, -1, false, diff)

	api.nvim_buf_set_option(buf, 'filetype', 'diff')
	api.nvim_buf_set_option(buf, 'modifiable', false)

	api.nvim_command("buffer " ..buf)

end

local function approve_diff()
	diffname = api.nvim_buf_get_var(0, 'diff-num')
	phab_command("diff-approve", diffname, "test")
end

return {
	update_task = update_task,
	sync_task = sync_task,
	create_task = create_task,
	get_diff = get_diff,
	approve_diff = approve_diff,
	get_path = get_path
}

