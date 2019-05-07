# README  

本文对于动态链接器的分析基于32位elf，glibc 2.9

## 参考资料  

1. linux elf(5)手册  
2. glibc 2.9 source 
3. google & baidu   

## 环境  

1. python2 with pwntools  
2. ida  
3. debian 9  x64

## 目录  

### dlruntime.md  

介绍了32位环境下elf动态链接器dl_runtime_resolve对全局偏移表的修复过程  

### instance.md

对一个实例运用先前介绍的知识z进行实验，完成ret2dlruntime对动态链接器的劫持  

### hack.py

完成攻击的脚本  

### test  

用于测试的的二进制文件  

---  

** enjoy ; ) **
