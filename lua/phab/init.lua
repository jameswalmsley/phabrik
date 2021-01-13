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
	local buf = api.nvim_create_buf(true, true) -- create new emtpy buffer

	api.nvim_buf_set_option(buf, 'bufhidden', 'wipe')


	-- get dimensions
	local width = api.nvim_get_option("columns")
	local height = api.nvim_get_option("lines")

	-- calculate our floating window size
	local win_height = math.ceil(height * 0.8 - 4)
	local win_width = math.ceil(width * 0.8)

	-- and its starting position
	local row = math.ceil((height - win_height) / 2 - 1)
	local col = math.ceil((width - win_width) / 2)

	-- set some options
	local opts = {
		style = "minimal",
		relative = "editor",
		width = win_width,
		height = win_height,
		row = row,
		col = col
	}

	-- and finally create it with buffer attached

	diffnum = vim.fn.expand('<cWORD>')

	local diff = phab_commandlist("diff", diffnum, "test")
	api.nvim_buf_set_lines(buf, 0, -1, false, diff)

	api.nvim_buf_set_option(buf, 'modifiable', false)
	api.nvim_buf_set_option(buf, 'filetype', 'diff')

	api.nvim_command("buffer " ..buf)


end

return {
	update_task = update_task,
	sync_task = sync_task,
	create_task = create_task,
	get_diff = get_diff,
	get_path = get_path
}

