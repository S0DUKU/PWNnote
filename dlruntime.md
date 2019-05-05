# about dl_runtime_resolve

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
     //动态段中dt_needed标签所标示的一些列依赖库，他被保存于当前模块link_map的
     //搜索范围之内，通常用于独立请求的符号搜索，当在依赖项被加载前，不会有任何
     //可用的入口点
    struct r_scope_elem l_searchlist;
    
    /* Dependent object that first caused this object to be loaded.  */
    //第一次唤起当前模块被加载的模块
    struct link_map *l_loader;
    /* This is an array defining the lookup scope for this link map.
       There are initially at most three different scope lists.  */
      //这个数组定义了当前模块用于lookup函数搜索的范围，最多有三个不同范围的列表
    struct r_scope_elem **l_scope;
    
    ......
    
};

```

