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

local function get_python()
	local command = "PYTHONPATH=" .. get_path() .. "/py/packages python3 "
	return command
end

local function get_command()
	local command = get_python() .. get_path() .. "/py/phab.py "
	return command
end

local function phab_command(command, args)
	return vim.fn.system(get_command() .. command .. " " .. args)
end

local function phab_commandlist(command, args)
	return vim.fn.systemlist(get_command() .. command .. " " .. args)
end


local api = vim.api

local function set_md_buffer_options(buf)
	vim.fn.setbufvar(buf, '&buftype', 'nofile')
	vim.fn.setbufvar(buf, '&buflisted', 1)
	vim.fn.setbufvar(buf, '&filetype', 'vimwiki')
	vim.fn.execute(buf .. "bufdo set syntax=markdown")
	vim.fn.execute(buf .. "bufdo setlocal nofoldenable")
	vim.fn.execute(buf .. "bufdo setlocal conceallevel=0")
	vim.fn.execute(buf .. "bufdo syntax match mkdRule \"\\s*[PTD]\\d\\+\\s*\"")
	vim.fn.execute("nnoremap <buffer> <Enter> :lua phab.navigate()<CR>")
end

local function get_diff(diffnum)

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

	vim.fn.execute("nnoremap <buffer> <Enter> :lua phab.navigate()<CR>")
end

local function dashboard()
	local buf = vim.fn.bufnr("Phabrik", 1)

	set_md_buffer_options(buf)

	local output = phab_commandlist("dashboard", "")
	api.nvim_buf_set_lines(buf, 0, -1, false, output)

	vim.fn.setbufvar(buf, '&modifiable', 0)

	local command = buf .. "bufdo file " .. vim.fn.fnameescape("Phabrik")
	vim.fn.execute(command)
	vim.fn.execute(buf .. "buffer")
	vim.fn.execute("nnoremap <buffer> <Enter> :lua phab.navigate()<CR>")
end

local function open_project(pnr)
	local buf = vim.fn.bufnr(pnr, 1)

	set_md_buffer_options(buf)

	local output = phab_commandlist("project", pnr)
	api.nvim_buf_set_lines(buf, 0, -1, false, output)

	vim.fn.setbufvar(buf, '&modifiable', 1)

	local command = buf .. "bufdo file " .. vim.fn.fnameescape(pnr)
	vim.fn.execute(command)
	vim.fn.execute(buf .. "buffer")
end

local function open_task(tasknr)
	local buf = vim.fn.bufnr(tasknr, 1)

	set_md_buffer_options(buf)

	local output = phab_commandlist("task", tasknr)
	api.nvim_buf_set_lines(buf, 0, -1, false, output)

	vim.fn.setbufvar(buf, '&modifiable', 1)

	local command = buf .. "bufdo file " .. vim.fn.fnameescape(tasknr)
	vim.fn.execute(command)
	vim.fn.execute(buf .. "buffer")
end

local function update_task()
	local tasknr = vim.fn.expand("%")
	local command = ":w !" .. get_command() .. "task --update " .. tasknr
	vim.fn.execute(command)

	open_task(tasknr)
end

local function create_task()
	local title = vim.fn.input("Task Title > ")
	local tasknr = phab_command("create", string.format("\"%s\"", title))
	open_task(tasknr)
end

local function navigate()
	local word = vim.fn.expand('<cWORD>')
	local line = vim.fn.getline('.')

	local match = word:match("T%d+")
	if(match) then
		return open_task(match)
	end

	local match = word:match("D%d+")
	if(match) then
		return get_diff(match)
	end

	local match = word:match("P%d+")
	if(match) then
		return open_project(match)
	end

	local match = line:match("T%d+")
	if(match) then
		return open_task(match)
	end

	local match = line:match("D%d+")
	if(match) then
		return get_diff(match)
	end

	print("Not a valid Phabrik link: ", word)

end

local function approve_diff()
	local diffname = api.nvim_buf_get_var(0, 'diffnum')
	phab_command("diff", "--approve " .. diffname)
end

local function apply_patch()
	local diffname = api.nvim_buf_get_var(0, 'diffnum')
	phab_command("patch", diffname)
end

local function diff_start_comment()
	local diffnum = api.nvim_buf_get_var(0, 'diffnum')
	vim.fn.execute("below split")
	local buf = vim.fn.bufnr(diffnum .. " - Comment", 1)

	vim.fn.setbufvar(buf, '&bufhidden', 'wipe')
	vim.fn.setbufvar(buf, '&buftype', 'nofile')
	vim.fn.setbufvar(buf, '&buflisted', 1)
	vim.fn.setbufvar(buf, 'diffnum', diffnum)
	vim.fn.setbufvar(buf, '&filetype', 'vimwiki')

	vim.fn.execute(buf .. "buffer")
	vim.fn.execute("autocmd BufLeave <buffer> lua phab.diff_close_comment()")
end

local function diff_close_comment()
	vim.fn.execute("bdelete")
end

local function install()
	local packages = "python-frontmatter unidiff phabricator"
	local cmd = "python3 -m pip install --target=" .. get_path() .. "/py/packages " .. packages
	return vim.fn.system(cmd)
end

return {
	get_path = get_path,
	update_task = update_task,
	create_task = create_task,
	open_task = open_task,
	open_project = open_project,
	get_diff = get_diff,
	approve_diff = approve_diff,
	apply_patch = apply_patch,
	diff_start_comment = diff_start_comment,
	diff_close_comment = diff_close_comment,
	navigate = navigate,
	dashboard = dashboard,
	install = install,
}

