# ROP
## ret2_dl_runtime_resolve

动态链接中的延迟链接过程：  
程序text节中call plt表中相应条目如call fgets.plt  
plt条目中有如下指令。

```

  Fgets.plt:  
	jmp		fgets.got
	push		fgets index
	jmp		xxxxx
  
 
```

延迟链接不会第一次加载程序时候就加载，而是通过plt，和got.plt节来对函数进行解析。解析后，修改got表内容为实际函数地址。  

**重定位表中偏移就是对应的got表项。**  

在第一次进行链接时候got表中存放的是plt项的下一条指令地址，所以会执行上面的push index，index为0实际是3即第四个,应为前三个有特殊用途。  

**got表前三个内容如下：**  
Got 0 存放 可执行文件动态段的地址，动态链接器利用该地址提取动态链接有关信息。  
Got 1 存放link map地址，动态链接器利用该结构地址对符号进行解析  
Got 2 存放指向动态链接器_dl_runtime_resolve()函数的地址，该函数用来解析动态链接库实际地址。  

Plt条目中的最后一条指令jmp xxxxx指向plt 0  

**Plt 0代码如下:**  

```
push  got 1  link_map
jmp 	got 2 dl_rumtime_resolve
```
解析后got变为实际地址  

Elf动态段的有一个程序头，动态段保存由类型elfn_dyn的结构体组成的数组。  

```
Typedef struct{
	elf32_sword d_tag;
	union{
		elf32_word d_val;
		elf32_addr d_ptr;
	}d_un;
}elf32_dyn;
```

d_ptr指向内存地址，给动态链接器各种需要的值，如果d_tag是d_symtab就是指向符号表，dynsym
动态链接器映射到内存中，首先会处理自己的重定位，应为它也是个共享库，接着获取动态段查找DT_NEED找到所有需要的共享库，并且获取共享库的动态段，和符号表信息。每加载一个就会生成一个link_map，将其存入一个链表中

### _dl_runtime_resolve  

_dl_runtime_resolve(link_map, reloc_arg)  

