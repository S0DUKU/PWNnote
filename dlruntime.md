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

//about link_map
/* Structure describing a loaded shared object.  The `l_next' and `l_prev'
   members form a chain of all the shared objects loaded at startup.

   These data structures exist in space used by the run-time dynamic linker;
   modifying them may have disastrous results.

   This data structure might change in future, if necessary.  User-level
   programs must avoid defining objects of this type.  */
   
   //link_map是一个用于描述可加载共享目标文件的结构，l_next,l_prev是一个链接了开始加载的所用共享目标文件，是一个单链表结构

```
