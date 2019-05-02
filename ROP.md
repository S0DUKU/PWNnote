# ROP
## ret2_dl_runtime_resolve

动态链接中的延迟链接过程：  
程序text节中call plt表中相应条目如call fgets.plt  
plt条目中有如下指令。

```

  Fgets.plt:  
	jmp		fgets.got
	push		fgets rel offset
	jmp		xxxxx
  
 
```

延迟链接不会第一次加载程序时候就加载，而是通过plt，和got.plt节来对函数进行解析。解析后，修改got表内容为实际函数地址。  

**重定位表中偏移就是对应的got表项。**  

在第一次进行链接时候got表中存放的是plt项的下一条指令地址，所以会执行上面的push rel oofset，offset为0实际是3即第四个,应为前三个有特殊用途。  

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


_dl_runtime_resolve(link_map, reloc_arg)  
具体实现在glibc-2.23/sysdeps/i386/dl-trampoline.S以一段汇编和内部函数_dl_fixup(struct link_map *l, ElfW(Word) reloc_arg)  

```
_dl_fixup(struct link_map *l, ElfW(Word) reloc_arg)
{
    // 首先通过参数reloc_arg计算重定位入口，这里的JMPREL即.rel.plt，reloc_offset即reloc_arg
    const PLTREL *const reloc = (const void *) (D_PTR (l, l_info[DT_JMPREL]) + reloc_offset);
    // 然后通过reloc->r_info找到.dynsym中对应的条目
    const ElfW(Sym) *sym = &symtab[ELFW(R_SYM) (reloc->r_info)];
    // 这里还会检查reloc->r_info的最低位是不是R_386_JUMP_SLOT=7
    assert (ELFW(R_TYPE)(reloc->r_info) == ELF_MACHINE_JMP_SLOT);
    // 接着通过strtab+sym->st_name找到符号表字符串，result为libc基地址
    result = _dl_lookup_symbol_x (strtab + sym->st_name, l, &sym, l->l_scope, version, ELF_RTYPE_CLASS_PLT, flags, NULL);
    // value为libc基址加上要解析函数的偏移地址，也即实际地址
    value = DL_FIXUP_MAKE_VALUE (result, sym ? (LOOKUP_VALUE_ADDRESS (result) + sym->st_value) : 0);
    // 最后把value写入相应的GOT表条目中
    return elf_machine_fixup_plt (l, result, reloc, rel_addr, value);
}
```
## link.h中的数据结构
```
struct r_scope_elem
{
  /* Array of maps for the scope.  */
  //scope用的map数组
  struct link_map **r_list;
  /* Number of entries in the scope.  */
  //map的数量
  unsigned int r_nlist;
};
```
```
struct link_map
  {
    /* These first few members are part of the protocol with the debugger.
       This is the same format used in SVR4.  */
      //共享文件加载基地址
    ElfW(Addr) l_addr;		/* Base address shared object is loaded at.  */
      //绝对文件名
    char *l_name;		/* Absolute file name object was found in.  */
      //动态段加载地址
    ElfW(Dyn) *l_ld;		/* Dynamic section of the shared object.  */
      //加载项链表
    struct link_map *l_next, *l_prev; /* Chain of loaded objects.  */

    /* All following members are internal to the dynamic linker.
       They may change without notice.  */
      //其他成员是对于动态链接器内部的，可能随时改变不受提醒
      
      .......
      
 ElfW(Dyn) *l_info[DT_NUM + DT_THISPROCNUM + DT_VERSIONTAGNUM
		      + DT_EXTRANUM + DT_VALNUM + DT_ADDRNUM];
    const ElfW(Phdr) *l_phdr;	/* Pointer to program header table in core.  */
    ElfW(Addr) l_entry;		/* Entry point location.  */
    ElfW(Half) l_phnum;		/* Number of program header entries.  */
    ElfW(Half) l_ldnum;		/* Number of dynamic segment entries.  */

    /* Array of DT_NEEDED dependencies and their dependencies, in
       dependency order for symbol lookup (with and without
       duplicates).  There is no entry before the dependencies have
       been loaded.  */
       //依赖项，在加载之前，没有数组项
    struct r_scope_elem l_searchlist;

    /* We need a special searchlist to process objects marked with
       DT_SYMBOLIC.  */
    struct r_scope_elem l_symbolic_searchlist;

    /* Dependent object that first caused this object to be loaded.  */
    //引发这个模块被加载的模块
    struct link_map *l_loader;
    
    .......
    
    /* Default array for 'l_scope'.  */
    struct r_scope_elem *l_scope_mem[4];
    /* Size of array allocated for 'l_scope'.  */
    size_t l_scope_max;
    /* This is an array defining the lookup scope for this link map.
       There are initially at most three different scope lists.  */
    struct r_scope_elem **l_scope;

    /* A similar array, this time only with the local scope.  This is
       used occasionally.  */
    struct r_scope_elem *l_local_scope[2];
    .......
      
```

## _dl_lookup_symbol_x




