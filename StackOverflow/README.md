# README  

## 环境  

1. python2 with pwntools
2. ida
3. debian x64
4. gcc 

## 目录  

### instance.md

对实例程序漏洞的利用过程,和有关讲解 

### stackOverflow

含有漏洞的二进制实例程序  

### stackOverflow.c

漏洞程序的源码，如果想要自行编译 请确保关闭必要的保护  

gcc -o stackOverflow -no-pie -m32 -z execstack -w stackOverflow.c

### hack.py

漏洞利用实现脚本

---  

** enjoy ; ) **  

