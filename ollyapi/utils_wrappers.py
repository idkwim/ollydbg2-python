#!/usr/bin/env python
# -*- coding: utf-8 -*-

#
#    utils_wrappers.py - All the functions that don't belong to other modules.
#    Copyright (C) 2012 Axel "0vercl0k" Souchet - http://www.twitter.com/0vercl0k
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <http://www.gnu.org/licenses/>.
#
from ctypes import *
from common import *
from utils_constants import *
from threads_constants import t_reg_p, t_reg
from memory_wrappers import FlushMemoryCache

# stdapi (int) InsertnameW(ulong addr,int type,wchar_t *s);
InsertnameW_TYPE = CFUNCTYPE(c_int, c_ulong, c_int, c_wchar_p)
InsertnameW = InsertnameW_TYPE(resolve_api('InsertnameW'))

# stdapi (int) Run(t_status status,int pass);
Run_TYPE = CFUNCTYPE(c_int, c_int, c_int)
Run_ = Run_TYPE(resolve_api('Run'))

# stdapi (t_module *) Findmainmodule(void);
Findmainmodule_TYPE = CFUNCTYPE(t_module_p)
Findmainmodule = Findmainmodule_TYPE(resolve_api('Findmainmodule'))

# stdapi (int) Checkfordebugevent(void);
Checkfordebugevent_TYPE = CFUNCTYPE(c_int)
Checkfordebugevent = Checkfordebugevent_TYPE(resolve_api('Checkfordebugevent'))

# oddata (wchar_t) arguments[ARGLEN];    // Command line passed to debuggee
_arguments = resolve_api('arguments')

# stdapi (int) Closeprocess(int confirm);
Closeprocess_TYPE = CFUNCTYPE(c_int, c_int)
Closeprocess = Closeprocess_TYPE(resolve_api('Closeprocess'))

# stdapi (ulong) Disasm(uchar *cmd,ulong cmdsize,ulong cmdip,uchar *cmddec,t_disasm *cmdda,int cmdmode,t_reg *cmdreg,t_predict *cmdpredict);
Disasm_TYPE = CFUNCTYPE(c_ulong, c_char_p, c_ulong, c_ulong, c_char_p, t_disasm_p, c_int, t_reg_p, t_predict_p)
Disasm = Disasm_TYPE(resolve_api('Disasm'))

# stdapi (ulong) Assemble(wchar_t *src,ulong ip,uchar *buf,ulong nbuf,int mode,wchar_t *errtxt);
Assemble_TYPE = CFUNCTYPE(c_ulong, c_wchar_p, c_ulong, c_char_p, c_ulong, c_int, c_wchar_p)
Assemble__ = Assemble_TYPE(resolve_api('Assemble'))

# stdapi (int) Assembleallforms(wchar_t *src,ulong ip,t_asmmod *model,int maxmodel,int mode,wchar_t *errtxt);
Assembleallforms_TYPE = CFUNCTYPE(c_int, c_wchar_p, c_ulong, t_asmmod_p, c_int, c_int, c_wchar_p)
Assembleallforms = Assembleallforms_TYPE(resolve_api('Assembleallforms'))

# stdapi (ulong)   Comparecommand(uchar *cmd,ulong cmdsize,ulong cmdip,t_asmmod *model,int nmodel,int *pa,int *pb,t_disasm *da);
Comparecommand_TYPE = CFUNCTYPE(c_ulong, c_char_p, c_ulong, c_ulong, t_asmmod_p, c_int, c_int_p, c_int_p, t_disasm_p)
Comparecommand = Comparecommand_TYPE(resolve_api('Comparecommand'))

# stdapi (int) Getanalysercomment(struct t_module *pmod,ulong addr,wchar_t *comment,int len);
Getanalysercomment_TYPE = CFUNCTYPE(c_int, t_module_p, c_ulong, c_wchar_p, c_int)
Getanalysercomment = Getanalysercomment_TYPE(resolve_api('Getanalysercomment'))

# stdapi (int) Getproccomment(ulong addr,ulong acall,wchar_t *comment,int len,int argonly);
Getproccomment_TYPE = CFUNCTYPE(c_int, c_ulong, c_ulong, c_wchar_p, c_int, c_int)
Getproccomment = Getproccomment_TYPE(resolve_api('Getproccomment'))

# oddata (t_run)   run; // Run status of debugged application
run_ = t_run.from_address(resolve_api('run'))

def InsertNameW(addr, type_, s):
    """
    That function is used to add label and comment directly on the disassembly
    (like with the shortcut ':' or ';')
    """
    return InsertnameW(
        c_ulong(addr),
        c_int(type_),
        c_wchar_p(s)
    )

def Run(status = STAT_RUNNING, pass_exception = 0):
    """
    Run the process, step-in, step-over, whatever
    """
    Run_(c_int(status), c_int(pass_exception))

    # required in order to update the state of the thread registers (retrieved with Threadregisters for example)
    # BTW, not sure it's supposed to be done this way though, I've found that in an OllyDBG2 reverse-engineering session.
    while CheckForDebugEvent() == 1:
        FlushMemoryCache()

def FindMainModule():
    """
    Get a cool structure filled with juicy information concerning
    the process being debugged ; you can find its ImageBase, real ImageBase, etc.
    Check t_module structure definition
    """
    r = Findmainmodule()

    if IsNullPointer(r):
        raise Exception("You haven't loaded any executable file")

    return r.contents

def CheckForDebugEvent():
    """
    Hum, this method seems to be very important, one of its purpose
    is to updated the thread registers retrieved thanks to Threadregisters()
    """
    return Checkfordebugevent()

def CloseProcess(confirm = 0):
    """
    Close the process being debugged
    """
    return Closeprocess(c_int(confirm))

def SetArguments(s):
    """
    Set the cmdline passed to the debuggee, exactly the same when you do "File > Set new arguments"
    """
    # XXX: maybe check if a process is loaded ?
    memset(c_void_p(_arguments), 0, ARGLEN * sizeof(c_wchar))
    wcsncpy(c_wchar_p(_arguments), c_wchar_p(s), ARGLEN - 1)
    
def Disasm_(c, address = 0):
    """
    Disassemble some x86 code thanks to the OllyDbg2 engine
    """
    di = t_disasm()
    reg = t_reg()
    predict = t_predict()

    buff = create_string_buffer(c)

    size_instr = Disasm(
        buff,
        len(buff) - 1, # create_string_buffer add a NULL byte at the end of the buffer
        c_ulong(address),
        None,
        pointer(di),
        29, # DA_TEXT | DA_OPCOMM | DA_DUMP | DA_MEMORY
        pointer(reg),
        pointer(predict)
    )

    return (size_instr, di.result)

def Assemble_(s, address = 0):
    """
    Assemble some x86 stuff
    """

    # the longuest x86 instruction is 15 bytes long
    code = create_string_buffer(15)

    # XXX: it should be enough (?)
    error_msg = (c_wchar * 100)()

    sizeof_assembled = Assemble__(
        c_wchar_p(s),
        c_ulong(address),
        code,
        len(code),
        1,
        error_msg
    )

    # you submit invalid x86 assembly
    if len(error_msg.value) > 0:
        return (0, 0, error_msg.value)

    return (code[:sizeof_assembled], sizeof_assembled, error_msg.value)

def AssembleAllForms(s, ip = 0):
    """
    Actually, I only use this function to obtain a t_asmod structure, to pass it
    at CompareCommand()
    """
    maxmodel = 0x80
    asmod = (t_asmmod * maxmodel)()

    # XXX: it should be enough (?)
    error_msg = (c_wchar * 100)()

    r = Assembleallforms(
        c_wchar_p(s),
        ip,
        cast(asmod, t_asmmod_p), # XXX: if you know a proper way, tell me!
        maxmodel,
        7,
        error_msg
    )

    if r == 0:
        raise Exception('Cannot assembled your instruction: %s' % error_msg.value)

    return asmod, r

def CompareCommand(cmd, cmdsize, cmdip, model, nmodel):
    """
    Compare command, used to search instruction accross the memory
    """
    dis = t_disasm()
    i1, i2 = c_int(), c_int()

    return Comparecommand(
        c_char_p(cmd),
        c_ulong(cmdsize),
        c_ulong(cmdip),
        cast(model, t_asmmod_p), # XXX: remember in AssembleAllForm we have an array of t_asmmod
        c_int(nmodel),
        c_int_p(i1),
        c_int_p(i2),
        t_disasm_p(dis)
    )

def GetAnalyserComment(addr):
    """
    Get an analyser comment with an address

    Example of comment you can retrieved:

    """
    buf = (c_wchar * 100)()
    r = Getanalysercomment(
        cast(None, t_module_p),
        c_ulong(addr),
        buf,
        c_int(100)
    )

    return buf.value

def GetProcComment(addr, acall = 0, argonly = 0):
    """
    Get comment generated for a specific Procedure

    Example of comment:
        004017A0  /$  55            PUSH EBP                                 ; breakpoints.004017A0(guessed void)
    """
    buf = (c_wchar * 100)()
    r = Getproccomment(
        c_ulong(addr),
        c_ulong(acall),
        buf,
        c_int(100),
        c_int(argonly)
    )

    return buf.value

def IsDebugeeFinished():
    """Is the debugee is finished ?"""
    return run_.status == STAT_FINISHED