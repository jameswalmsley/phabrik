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

local function phab_command(command, args)
	return vim.fn.system("python3 " .. get_path() .. "/py/phab.py " .. command .. " " .. args)
end

local function phab_commandlist(command, args)
	return vim.fn.systemlist("python3 " .. get_path() .. "/py/phab.py " .. command .. " " .. args)
end

local function update_task()
	vim.api.nvim_command("write")
	phab_command("update", get_task_id() .. " " .. get_file_path())
end

local function sync_task()
	phab_command("sync", get_task_id() .. " " .. get_file_path())
end

local function create_task()
	local title = vim.fn.input("Task Title > ")
	local output = phab_command("create", "Txxx " .. string.format("\"%s\"", title))
	local path = string.format("%s/%s", get_file_folder(), output)
	vim.api.nvim_command("edit " .. path)
end

local api = vim.api

local function get_diff()
	local diffnum = vim.fn.expand('<cWORD>')

	local buf = vim.fn.bufnr(diffnum, 1)

	vim.fn.setbufvar(buf, '&bufhidden', 'wipe')
	vim.fn.setbufvar(buf, '&buftype', 'nofile')
	vim.fn.setbufvar(buf, '&buflisted', 1)
	vim.fn.setbufvar(buf, 'diffnum', diffnum)


	local diff = phab_commandlist("diff", diffnum)
	api.nvim_buf_set_lines(buf, 0, -1, false, diff)

	vim.fn.setbufvar(buf, '&filetype', 'diff')
	vim.fn.setbufvar(buf, '&modifiable', 0)

	local command = buf .. "bufdo file " .. vim.fn.fnameescape(diffnum)
	vim.fn.execute(command)
	vim.fn.execute(buf .. "buffer")

end

local function approve_diff()
	local diffname = api.nvim_buf_get_var(0, 'diffnum')
	phab_command("diff", "--approve " .. diffname)
end

local function apply_patch()
	local diffname = api.nvim_buf_get_var(0, 'diffnum')
	phab_command("patch", diffname)
end

return {
	update_task = update_task,
	sync_task = sync_task,
	create_task = create_task,
	get_diff = get_diff,
	approve_diff = approve_diff,
	apply_patch = apply_patch,
	get_path = get_path
}

