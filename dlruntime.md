# dl_runtime_resolve简要分析
## 资料

glibc 2.9 source
linux elf 手册
&各种百度搜索

基于32位elf，64位一些结构会略有不同，新手学习，如果有理解错误，请师傅们帮忙指出。

**elf执行时动态绑定简要分析**


## 动态链接的过程  

动态链接中起到核心作用的是got节和plt节，链接器为所有共享目标文件(shared object)中未定义的(undef)外部符号生成一个got表，每个got表项存储符号在运行时的实际值(地址)，plt表中的每一项实际是一段指令，每个外部函数都有一个对应的plt项他指导系统完成动态链接，或是执行外部函数。

### plt节

plt节中一组代码如下所示：  

```
 fgets.plt:
       jmp      fgets.got
       push     fgets.rel offset
       jmp      xxxxx ;plt[0]的地址这里存储的是调用动态链接器的过程指令

```
如上所示，如果程序调用了fgets函数(代码段中实际调用了fgets.plt的地址)，并且fgets使用动态链接方式，linux的延迟绑定机制(直到第一次调用才会完成重定位)会为当前函数调用动态链接器已完成对got表的修改。

由于所有函数在完成绑定之前，他们对应got表的值实际上是对应plt项的第二条指令，即如上push xxxx，该指令会将fgets函数在重定位表中的偏移压入栈上，而后执行jmp plt[0]，去执行plt[0]位置的代码。

plt[0]保存的代码如下:

```
       push  got 1  ;link_map
       jmp   got 2  ;dl_rumtime_resolve

```

压got[1] (保存了本模块的link_map结构，后文介绍)中保存的值入栈，跳转执行got[2]中的函数，实际上就是动态链接器dl_runtime_resolve的地址。dl_runtime_resolve的实现在glibc源代码中的dl-trampoline.c中，是一段汇编形式的代码，他调用了内部函数 _dl_fixup(struct link_map \*__unbounded l, ElfW(Word) reloc_offset)来处理动态链接，刚刚压入栈的值就是作为他的参数。完成链接后，对应got表项中的值会变为实际函数地址，此后对plt表项的调用，将直接跳转到实际got表项的函数内，不会再进行重复绑定。


---

## link_map结构简要分析  
有关link_map的定义位于glibc源码的link.h中  

### r_scope_elem

```
/* Structure to describe a single list of scope elements.  The lookup
   functions get passed an array of pointers to such structures.  */
   //描述一个特定范围的单链表结构，lookup函数往往需要传递一个保存这种结构的数组作为参数
struct r_scope_elem
{
  /* Array of maps for the scope.  */
  //用于描述范围的maps数组
  struct link_map **r_list;
  /* 这个范围的入口点个数  */
  unsigned int r_nlist;
  //这会在link_map中作为成员存在
};

```
### link_map

```

//about link_map
   
   //link_map是一个用于描述可加载共享目标文件的结构，l_next,l_prev是一个链接了
   //开始加载的所用共享目标文件，是一个单链表结构,这个单链表结构一般被用于动态链接器
   //修改他们可能会带来灾难性的后果
   
   //由于link_map成员较多，较为复杂，需要很多基础知识，甚至有包括线程安全。
   //我也没全部搞懂，所以介绍一部分
   
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

    /* This is an element which is only ever different from a pointer to
       the very same copy of this type for ld.so when it is used in more
       than one namespace.  */
    struct link_map *l_real;

    /* Number of the namespace this link map belongs to.  */
      //这link map属于的命名空间个数
     
    ElfW(Dyn) *l_info[DT_NUM + DT_THISPROCNUM + DT_VERSIONTAGNUM
		      + DT_EXTRANUM + DT_VALNUM + DT_ADDRNUM];
     //这个数组用于快速访问动态段的信息，在lookup系列函数中会频繁使用
     //它的有关定义还包含了一系列用于访问信息的功能宏。
     
     /* Array of DT_NEEDED dependencies and their dependencies, in
       dependency order for symbol lookup (with and without
       duplicates).  There is no entry before the dependencies have
       been loaded.  */
     //依赖项及其依赖项的数组，按符号查找的依赖项顺序排列(有和没有重复)。
     //在加载依赖项之前没有条目。
    struct r_scope_elem l_searchlist;
    
    /* Dependent object that first caused this object to be loaded.  */
    //第一次唤起当前模块被加载的模块
    struct link_map *l_loader;
    /* This is an array defining the lookup scope for this link map.
       There are initially at most three different scope lists.  */
      //这个数组定义了当前模块用于lookup函数搜索的范围，最初最多有三个不同范围的列表
    struct r_scope_elem **l_scope;
    
    ......
    
};

```

### 有关宏定义
定义在ldsodef.h头文件中  

```
//宏访问link_map成员并计算地址
# define D_PTR(map, i) ((map)->i->d_un.d_ptr + (map)->l_addr)
#else
# define D_PTR(map, i) (map)->i->d_un.d_ptr
#endif

/* Result of the lookup functions and how to retrieve the base address.  */
//lookup系列函数的返回值
typedef struct link_map *lookup_t;
#define LOOKUP_VALUE(map) map
#define LOOKUP_VALUE_ADDRESS(map) ((map) ? (map)->l_addr : 0)

```
## _dl_fixup(struct link_map *__unbounded l, ElfW(Word) reloc_offset)简要分析

dl_runtime_resolve的内部调用函数dl_fixup的实现在dl-runtime.c中  
内容比较多，我也有些不清楚，大致分析出执行逻辑

```
#ifndef ELF_MACHINE_NO_PLT
DL_FIXUP_VALUE_TYPE
__attribute ((noinline)) ARCH_FIXUP_ATTRIBUTE
_dl_fixup (
# ifdef ELF_MACHINE_RUNTIME_FIXUP_ARGS
	   ELF_MACHINE_RUNTIME_FIXUP_ARGS,
# endif
	   /* GKM FIXME: Fix trampoline to pass bounds so we can do
	      without the `__unbounded' qualifier.  */
	   struct link_map *__unbounded l, ElfW(Word) reloc_offset)
{
    //参数link_map ， 重定位表中偏移
    //通过link_map，获得动态链接库中的符号表位置，link_map中有成员
    //指向动态段，包含各种动态链接所需要的信息
    
    
  const ElfW(Sym) *const symtab
    = (const void *) D_PTR (l, l_info[DT_SYMTAB]);
    
    //获取动态库的字符串表
  const char *strtab = (const void *) D_PTR (l, l_info[DT_STRTAB]);

    //获得重定位项的地址，宏转化为l->l_info[DT_JMPREL]+reloc_offset
  const PLTREL *const reloc
    = (const void *) (D_PTR (l, l_info[DT_JMPREL]) + reloc_offset);
    //根据重定位项目的r_info字段中的偏移查找符号表中的符号项
  const ElfW(Sym) *sym = &symtab[ELFW(R_SYM) (reloc->r_info)];
  //利用r_offset字段获得重定位需要修改的地址
  void *const rel_addr = (void *)(l->l_addr + reloc->r_offset);
  
  //lookup函数的返回结果
  lookup_t result;
  /* The type of the return value of fixup/profile_fixup.  */
  //#define DL_FIXUP_VALUE_TYPE ElfW(Addr)
  
  DL_FIXUP_VALUE_TYPE value;
  //简单的plt字段检查
  assert (ELFW(R_TYPE)(reloc->r_info) == ELF_MACHINE_JMP_SLOT);
  
  .......
  
  //在范围内搜索符号，定义在dl-lookup.c中
  //参数:  		字符串表，符号表项st_name字段，模块link_map，搜索范围,
  //					版本信息.....
  result = _dl_lookup_symbol_x (strtab + sym->st_name, l, &sym, l->l_scope,
				    version, ELF_RTYPE_CLASS_PLT, flags, NULL);

  .......
  //对result做一些收尾处理，最后修复plt表返回
  
  return elf_machine_fixup_plt (l, result, reloc, rel_addr, value);
  
  }
  
  ```
## elf中常见的信息结构

有关elf的结构定义在elf.h中

### elf动态段
由elf程序头表中保存的PT_DYNAMIC段(动态段)，包含了动态链接器的所需的信息。

运行时所需的共享库列表，全局偏移表(got)地址，重定位条目信息  

条目结构  

```
typedef struct {
  elf32_sword  d_tag
  union{
  elf32_word  d_val
  elf32_addr  d_ptr
  }d_un;
  }elf32_dyn;
  
```

d_tag控制d_un的含义  

DT_HASH 		符号散列表地址   
**DT_STRTAB		字符串表的地址**  
**DT_SYMTAB		符号表地址**  
DT_RELA			相对地址重定位表的地址  
DT_STRSZ 		字符串表的字节大小  
DT_INIT			初始化函数的地址
DT_FINI 		终止函数的地址
DT_SONAME 		共享目标文件名的字符串表偏移量
**DT_JMPREL		仅用于plt的重定位条目地址**
......

.dynsym节 保存从共享库导入动态符号的信息  
.dynstr节 保存动态符号字符串表  

```
typedef struct
{
  Elf32_Word	st_name;		/* 字符串表名字节偏移,0表示未定义 */
  Elf32_Addr	st_value;		/* 符号值，位置或者地址偏移 */
  Elf32_Word	st_size;		/* 符号大小 */
  unsigned char	st_info;		/* 制定符号类型以及绑定属性 */
  unsigned char	st_other;		/* 符号可见性 */
  Elf32_Section	st_shndx;		/* 对应节头表索引 */
  
} Elf32_Sym;  

/*
符号类型  
STT_NOTYPE 符号类型未定义  
STT_FUNC 表示该符号与函数或者其他可执行代码关联   
STT_OBJECT 该符号与数据目标文件关联  
符号绑定  
STB_LOCAL 本地符号在目标文件外不可见，如static  
STB_GLOBAL 全局符号  
STB_WEAK 弱全局  
*/  

//重定位条目 无addend情况下

typedef struct
{
  Elf32_Addr	r_offset;		/* 相对基地址偏移地址 */
  Elf32_Word	r_info;			/* 符号表索引 */
} Elf32_Rel;

```

## 总结

1.dl_runtime_resolve动态链接执行时内部调用dl_fixup函数完成对未定义符号的修复操作。  

2.传入参数reloc_offset指向重定位表项中需要修改的重定位条目。  

3.根据这个重定位条目，获得对应符号表中的符号项信息，和需要修改的实际地址。  

4.通过符号项和字符串表获得符号名，传入符号项和相关参数调用_dl_lookup_symbol_x在本模块的link_map制定范围内搜索符号的定义。  

5.最后完成符号值修改，完成重定位。   





