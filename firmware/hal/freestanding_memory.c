/* SPDX-License-Identifier: GPL-3.0-or-later
 * Minimal compiler ABI helpers for the standalone bench build. */
#include <stddef.h>
void *memset(void *dst,int value,size_t n){volatile unsigned char *p=dst;for(size_t i=0;i<n;i++)p[i]=(unsigned char)value;return dst;}
void *memcpy(void *dst,const void *src,size_t n){volatile unsigned char *d=dst;const volatile unsigned char *s=src;for(size_t i=0;i<n;i++)d[i]=s[i];return dst;}
void __aeabi_memclr4(void *dst,size_t n){(void)memset(dst,0,n);}
void __aeabi_memcpy(void *dst,const void *src,size_t n){(void)memcpy(dst,src,n);}
