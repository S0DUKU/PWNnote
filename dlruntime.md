# about dl_runtime_resolve

基于32位elf，64位一些结构会略有不同

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

