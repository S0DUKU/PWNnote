# dl_runtime_resolve实例分析
## IDA静态分析

使用ida打开实例程序pwn，查看程序节视图，找到动态段，动态段是可加载的一般标记为load这里手动改名为.dynamic

---  

![](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/1.png)  

---

跟踪进入动态段，表项如下所示  

---  

![](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/2.png)  

---  

每个动态段表项结构如前面介绍所示有一个d_tag字段和d_union联合体构成，d_tag的值标示了d_un值的意义  

更具d_tag为DT_JMPREL值的条目跟踪进入，动态链接所用的重定位表  

---

![](https://github.com/S0DUKU/PWNnote/blob/master/ROP/ret2dlruntime/images/3.png)  

---  



