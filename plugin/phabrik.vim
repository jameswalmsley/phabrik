if exists('g:phabrik_loaded')
  finish
endif

let g:phabrik_loaded = 1

let g:phabrik_path = fnamemodify(resolve(expand('<sfile>:p')), ':h')
let g:phabrik_filetype = 'vimwiki'

function! phabrik#get_path()
  return g:phabrik_path . "/.."
endfunction

function! phabrik#python()
  return "PYTHONPATH=" . phabrik#get_path() . "/py/packages python3 "
endfunction

function! phabrik#command()
  return "" . phabrik#python() . phabrik#get_path() . "/py/phab.py "
endfunction

function! phabrik#phab(command, args)
  return system(phabrik#command() . a:command . " " . a:args)
endfunction

function! phabrik#phablist(command, args)
  return systemlist(phabrik#command() . a:command . " " . a:args)
endfunction

function! s:buf_switch_to(buf)
  execute(a:buf . 'buffer')
endfunc

function! s:push_buf(buf)
  let cur_buf = bufnr("%")
  call s:buf_switch_to(a:buf)
  return cur_buf
endfunc

function! s:pop_buf(buf)
  if bufwinnr(a:buf) > 0
    call s:buf_switch_to(a:buf)
  endif
endfunc

function! s:set_md_buffer_options(buf)
  call setbufvar(a:buf, '&bufhidden', 'hide')
  call setbufvar(a:buf, '&buftype', 'nofile')
  call setbufvar(a:buf, '&buflisted', 1)
  call setbufvar(a:buf, '&filetype', g:phabrik_filetype)
  call setbufvar(a:buf, '&syntax', 'markdown')
  let cur_buf = s:push_buf(a:buf)
  setlocal nofoldenable
  setlocal conceallevel=0

  " Syntax matching rule for Phabricator wiki links.
  syntax match mkdRule "\s*[PTD]\d\+\s*"
  nnoremap <buffer> <Enter> :call phabrik#navigate()<CR>

  call s:pop_buf(cur_buf)
endfunction


function! s:buf_set_lines(buf, text, modifiable)
  let cur_buf = s:push_buf(a:buf)

  call setbufvar(a:buf, '&modifiable', 1)
  %delete _
  call setline('.', a:text)
  call setbufvar(a:buf, '&modifiable', a:modifiable)

  call s:pop_buf(cur_buf)
endfunc

function! s:buf_set_title(buf, title)
  let command = a:buf . "bufdo file " . fnameescape(a:title)
  execute(command)
endfunc

function! s:dashboard_buf_update(buf)
  let output = phabrik#phablist("dashboard", "")
  call s:buf_set_lines(a:buf, output, 0)
endfunc

function! phabrik#dashboard()
  let buf = bufnr("Phabrik", 1)
  call s:set_md_buffer_options(buf)
  call s:dashboard_buf_update(buf)
  call s:buf_set_title(buf, "Phabrik")
  call s:buf_switch_to(buf)
endfunc

function! phabrik#diff_get(diffnum)
  let buf = bufnr(a:diffnum, 1)

  call setbufvar(buf, '&bufhidden', 'hide')
  call setbufvar(buf, '&buftype', 'nofile')
  call setbufvar(buf, '&buflisted', 1)
  call setbufvar(buf, 'diffnum', a:diffnum)

  let diff = phabrik#phablist("diff", a:diffnum)

  call setbufvar(buf, '&modifiable', 1)

  call s:buf_set_lines(buf, diff, 0)

  call execute(buf . "buffer")

  call setbufvar(buf, '&filetype', 'diff')

  let command = buf . "bufdo file " . fnameescape(a:diffnum)
  call execute(command)

  call execute("nnoremap <buffer> <Enter> :call phabrik#navigate()<CR>")
endfunc

function! s:diff_action(action)
  let diffname = getbufvar("%", 'diffnum')
  phabrik#phab("diff", "--" . action . " " . diffname)

endfunc

function! phabrik#diff_plan_changes()
  s:diff_action("plan-changes")
endfunc

function! phabrik#diff_request_review()
  s:diff_action("request-review")
endfunc

function! phabrik#diff_close()
  s:diff_action("close")
endfunc

function! phabrik#diff_reopen()
  s:diff_action("reopen")
endfunc

function! phabrik#diff_abandon()
  s:diff_action("abandon")
endfunc

function! phabrik#diff_approve()
  s:diff_action("approve")
endfunc

function! phabrik#diff_reclaim()
  s:diff_action("reclaim")
endfunc

function! phabrik#diff_request_changes()
  s:diff_action("request-changes")
endfunc

function! phabrik#diff_commandeer()
  s:diff_action("commandeer")
endfunc

function! phabrik#diff_resign()
  s:diff_action("resign")
endfunc

function! phabrik#diff_patch()
  s:diff_action("patch")
endfunc

function! s:task_buf_update(buf, tasknr)
  let output = phabrik#phablist("task", a:tasknr)
  call s:buf_set_lines(a:buf, output, 1)
endfunc

function! phabrik#task_open(tasknr)
  let buf = bufnr(a:tasknr, 1)

  call s:set_md_buffer_options(buf)

  call setbufvar(buf, '&modifiable', 1)

  call s:task_buf_update(buf, a:tasknr)

  call s:buf_switch_to(buf)
endfunc

function! phabrik#task_create()
  let title = input("Task Title > ")
  let tasknr = phabrik#phablist("create", "\"" . title . "\"")

  call phabrik#task_open(tasknr[0])
endfunc

function! phabrik#task_update()
  let buf = bufnr("%")
  let tasknr = expand("%")
  let pos = getcurpos()
  execute(":w !" . phabrik#command() . "task --update " . tasknr)
  call s:task_buf_update(buf, tasknr)
  call setpos('.', pos)
endfunc

function! phabrik#project_open(projnr)
  let buf = bufnr(a:projnr, 1)

  call s:set_md_buffer_options(buf)

  let output = phabrik#phablist("project", a:projnr)
  call s:buf_set_lines(buf, output, 0)

  execute(buf . "bufdo file " . fnameescape(a:projnr))
  execute(buf . "buffer")
endfunc

function! phabrik#navigate()
  let word = expand('<cWORD>')
  let line = getline('.')

  let regex = '\s*[TDP]\d\+\s*'

  let match = matchstr(word, regex)
  if match == ''
    let match = matchstr(line, regex)
    if match == ''
      echo "No Phabricator Link found!"
      return
    endif
  endif

  echo "Phabrik -> " . match

  if match[0] == 'D'
    return phabrik#diff_get(match)
  endif

  if match[0] == 'T'
    return phabrik#task_open(match)
  endif

  if match[0] == 'P'
    return phabrik#project_open(match)
  endif

endfunc

