# protect

介绍linux下的常见安全策略，关于这些策略的资料和原文，可以在目录下找到，或者通过  
谷歌百度搜索查询  

---  

## ALSR  

以下内容大部分引用自  
ASLR Smack & Laugh Reference  
Seminar on Adavanced Exploitation Techniques  
Tilo  Müller

address space layout randomization (ALSR) 地址空间布局随机化技术在现代是一种重要的  
用于f预防缓冲区漏洞利用的技术   

aslr并不是不安全代码的一种代替手段，但是他的确可以提供对已存在或未公布的还没有被   
修复漏洞的保护，alsr的主要目的是将随机化引用到进程的地址空间内，这使得许多常规漏  
洞的利用导致进程崩溃，而不是执行恶意代码  

aslr实现于linux内核版本2.6.12 是pax项目的一个组成(一个完整的安全补丁)，微软实现于win  
dows vista beta 2,虽然只用可执行文件被特定链接为aslr打开才行。  

### ALSR的工作方式

alsr可以被禁用通过在引导时传递 norandmaps 参数或者在运行时 通过 echo 0 > /proc/sys/kernel/randomize_va_space  

更具paxt项目的要求yc原始的alsr应该包括RANDEXEC,RANDMMAP,RANDUSTACK,RAND  
STACK  

randexec/randmmap     -   code/data/bss  segments   

randexec/randmmap     -   heap   

randmmap                     -   libraries,heap thread stacks  shared memory   

randustack                    -   user stack  

randkstack                    -   kernel  stack   

在目前版本的linux内核中还没有被全部实现，这可以让我们尝试return into non-randomized areas  
返回未随机化的区域  


### 暴力搜索  brute force

经过测试发现，32位下后24位被随机化，2^24中可能性，如果可以进行如此多的尝试，是可以  
爆破处缓冲区地址的,并且alsr有个特性(这段来自于international conference on security and privacy in communication networks 2014) 随机化只会随机一个前缀页的大小,4k(2^12 绝大部分intel架构)  
也就意味后12位不变，可以用这个特性确定libc版本(搜索libc数据库)，有些现代操作系统将其扩  
展至20位，只有4位不变    

### 拒绝服务  denial of service  

持续输入只溢出缓冲区，主要用于探测程序溢出点  

### 返回进入未随机化的内存  return into non-randomized memory  

虽然栈空间被随机化了但是还有许多空间在仅有alsr的情况下并没有随机化，比如  
heap,bss,data,text这些段的空间并没有被随机化  

可以通过返回执行这些空间中的代码片段来编写恶意代码，以此衍生的各种技术可以在其他目录下  
看到演示  

---  


