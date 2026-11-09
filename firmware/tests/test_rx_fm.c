#include "../rf/rx_fm.h"
#include <assert.h>
static unsigned count,fail_at;
static int backend(void *user,const d578_rx_op *op){(void)user;assert(op->kind<3&&op->bank<4);count++;return count==fail_at?-7:0;}
int main(void){
 for(unsigned n=1;n<=225;n++){count=0;fail_at=n;assert(d578_rx_reset(backend,0)==-7);assert(count==n);}
 count=0;fail_at=0;assert(d578_rx_reset(backend,0)==0);assert(count==225);
 count=0;assert(d578_rx_tune(2,14550000,backend,0)==-1);assert(d578_rx_tune(0,17500000,backend,0)==-1);assert(d578_rx_tune(1,39999999,backend,0)==-1);assert(d578_rx_tune(0,14550000,0,0)==-1);assert(!count);
 assert(d578_rx_fm_mode(2,0,backend,0)==-1);assert(d578_rx_threshold(2,100,backend,0)==-1);assert(!count);
 for(unsigned n=1;n<=12;n++){count=0;fail_at=n;assert(d578_rx_tune(0,14550000,backend,0)==-7);assert(count==n);}
 for(unsigned b=0;b<2;b++){
  count=0;fail_at=0;assert(d578_rx_begin(b,1,120,backend,0)==0);unsigned total=count;
  for(unsigned n=1;n<=total;n++){count=0;fail_at=n;assert(d578_rx_begin(b,1,120,backend,0)==-7);assert(count==n);}
  count=0;fail_at=0;assert(d578_rx_start(b,backend,0)==0);total=count;
  for(unsigned n=1;n<=total;n++){count=0;fail_at=n;assert(d578_rx_start(b,backend,0)==-7);assert(count==n);}
 }
 assert(!d578_rx_squelch_update(0,2,0,511,70));return 0;
}
