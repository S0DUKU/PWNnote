# dl_runtime_resolve实例分析
## IDA静态分析

使用ida打开实例程序pwn，查看程序节视图，找到动态段，动态段是可加载的一般标记为load这里手动改名为.dynamic

---  

![1.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/1.png)  

---

跟踪进入动态段，表项如下所示  

---  

![2.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/2.png)  

---  

每个动态段表项结构如前面介绍所示有一个d_tag字段和d_union联合体构成，d_tag的值标示了d_un值的意义  

更具d_tag为DT_JMPREL值的条目跟踪进入，动态链接所用的重定位表  

---

![3.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/3.png)  

---  

重定位项结构入elf.h中定义的那样包含r_offset和r_info成员，查看read函数的重定位表项，r_info的高8位保存了read在符号表中的索引，低8位表示了符号绑定所必需的信息，r_offset定位了重定位时需要修改的位置，我们更具 r_info >> 8 计算获得索引为 1, Elf32_Sym符号表条目结构的大小为16字节(可以通过编写一个简单c程序获得),所以read的符号表项位于符号表的 1 * 16 偏移处，如下所示0x1dc-0x1cc 16

---  

![5.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/5.png)  

---  

条目第一个成员时read在字符串表中的偏移，剩余的条目是符号表所描述的其他字段  

回到重定位条目，他的第一个r_offset描述的是需要修复的位置，跟踪进入，他刚好就是got表中的read所在的条目。

---  

![4.png](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/4.png)  

---  

之前提到的dl_runtime_resolve并没有对这些表项的边界做过多的检查检查，内部函数也就实际上使用reloc_offset这个参数找到重定位表并根据重定位条目获得符号字符串并进一步做dl-symbol-lookup，符号搜索，获得符号字符串的流程正如上方所示，所以我们可以通过伪造所需的这些数据结构，来完成ret2dl_runtime_resolve攻击。  

## ret2dl_runtime_resolve  

由于我们测试程序是partial relo 所以并不能对动态段做写操作，所以可以通过伪造所需要的重定位结构体来完成攻击操作。  

### 伪造

.bss段 开始地址 0x804a020

我们将重定位修改的位置设置为 0x804a0b0
我们让重定位条目开始于 0x804a0c0

```
{
    r_offset = 0x804a0b0  //重定位修改的地址 4bytes
    //重定位表基地址 0x8048314 符号表基地址0x80481CC
    //我们把符号表条目放置于0x804a0d0 计算符号表索引(0x804a0d0 - 0x80481cc)/16 elf32_sym结构体大小为16
    r_info = index << 8 + 7(这个值的详细信息在libc中有定义，这里直接仿造其他函数)
           //符号表索引，和绑定类型
    
   }




