#include<stdio.h>

typedef void __attribute__((__stdcall__)) (*cal)(char * a,char b) ;

void vuln(){
	char func[] = "U\x89\xe0\x83\xc0\x08\x89\xc3\x83\xc3\x04\x8b\x00\x8b\x1b\x01\x18]\xc3";
	char buf[] = "\0\0\0\0\0\0";
	char a = 0;
	char b = 0;

	cal add = (cal)func;

	puts("input your char:");
	read(0,&b,0x100);
	puts("input your magic char:");
	read(0,&a,0x100);

	puts("the result of the magic is:");

	add(&b,a);

	putchar(b);
	putchar('\n');

	return;	
}


int __attribute__((__stdcall__)) main(){

	puts("welcome my friend,let's do some magic ;)");
	vuln();
	return 0;
}
