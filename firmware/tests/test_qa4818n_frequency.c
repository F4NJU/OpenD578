#include "../rf/qa4818n_frequency.h"
#include "../rf/qa4818n_transport.h"
#include <assert.h>
#include <string.h>

typedef struct {unsigned count; uint8_t bank, reg[2]; uint16_t value[2];} Recorder;
static bool record(void *ctx, uint8_t bank, uint8_t reg, uint16_t value) {
    Recorder *r = (Recorder *)ctx;
    if (r->count >= 2) return false;
    r->bank=bank; r->reg[r->count]=reg; r->value[r->count]=value; r->count++;
    return true;
}
static void check(uint32_t hz,uint16_t hi,uint16_t lo) {
    uint16_t a=0,b=0;
    uint64_t h=0;
    assert(qa4818_encode_frequency_at1846s(hz,&a,&b));
    assert(a==hi && b==lo);
    assert(qa4818_decode_frequency_halfhz(a,b,&h));
    assert(h == (uint64_t)hz*2);
}
int main(void) {
    check(38550000,0x0009,0x6960);
    check(38850000,0x0009,0x7C20);
    check(145500000,0x0023,0x85C0);
    check(435000000,0x006A,0x3380);
    check(184050000,0x002C,0xEF20);
    check(473550000,0x0073,0x9CE0);
    uint16_t h=0,l=0;
    assert(!qa4818_encode_frequency_at1846s(145500000,0,&l));
    assert(!qa4818_encode_frequency_at1846s(145500000,&h,0));
    qa4818_frequency_plan_t plan;
    assert(!qa4818_plan_frequency_at1846s(4,145500000,&plan));
    assert(qa4818_plan_frequency_at1846s(2,145500000,&plan));
    uint8_t frame[3];
    assert(qa4818_pack_write_at1846s(plan.writes[0].reg,plan.writes[0].value,frame));
    assert(frame[0]==0x29 && frame[1]==0x00 && frame[2]==0x23);
    assert(!qa4818_pack_write_at1846s(0x80,0,frame));
    Recorder r={0};
    qa4818_transport_t t={record,&r,false};
    assert(!qa4818_apply_plan_to_bench(&t,&plan));
    assert(r.count==0);
    t.allow_experimental_writes=true;
    assert(qa4818_apply_plan_to_bench(&t,&plan));
    assert(r.count==2 && r.bank==2 && r.reg[0]==0x29 && r.reg[1]==0x2A);
    assert(r.value[0]==0x23 && r.value[1]==0x85C0);
    return 0;
}
