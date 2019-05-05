# about dl_runtime_resolve
##资料

glibc 2.9 source
《linux二进制分析》
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
  result = _dl_lookup_symbol_x (strtab + sym->st_name, l, &sym, l->l_scope,
				    version, ELF_RTYPE_CLASS_PLT, flags, NULL);

  .......
  
  return elf_machine_fixup_plt (l, result, reloc, rel_addr, value);
  
  }
  
  ```


