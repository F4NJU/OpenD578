/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "../hal/audio_control.h"
#include <assert.h>
#include <string.h>
typedef struct {size_t calls;size_t fail_at;} sink;
static int emit(void *user,const d578_audio_op *op)
{
    sink *s=user;assert(op->kind==D578_RF_WRITE);++s->calls;
    return s->calls==s->fail_at?-7:0;
}
int main(void)
{
    d578_audio_plan p;assert(d578_audio_fm_microphone(4,54,&p));
    size_t done=99;sink s={0,3};assert(d578_audio_apply(&p,emit,&s,&done)==-7);
    assert(done==2 && s.calls==3); /* fourth operation must never be sent */
    s=(sink){0,99};assert(d578_audio_apply(&p,emit,&s,&done)==0);assert(done==4 && s.calls==4);
    d578_audio_plan before=p;assert(!d578_audio_fm_microphone(6,54,&p));assert(memcmp(&before,&p,sizeof(p))==0);
    assert(!d578_audio_fm_microphone(4,64,&p));assert(memcmp(&before,&p,sizeof(p))==0);
    uint8_t v=77;assert(!d578_audio_volume_level(4096,&v));assert(v==77);assert(!d578_audio_volume_code(33,&v));assert(v==77);
    d578_audio_context c={0};c.speakers=(d578_speakers)-1;assert(!d578_audio_enable(&c,0,false,&p));assert(memcmp(&before,&p,sizeof(p))==0);
    c.speakers=D578_BOTH_SPEAKERS;c.path=(d578_mic_path)2;assert(!d578_audio_mic_path(&c,0,false,&p));
    assert(!d578_audio_enable(0,0,false,&p));assert(!d578_audio_fm_microphone(1,54,0));assert(!d578_audio_volume_level(1,0));assert(!d578_audio_mute(0,false,0));
    assert(d578_audio_apply(0,emit,&s,&done)==-1 && done==0);assert(d578_audio_apply(&p,0,&s,&done)==-1);
    p.count=5;s.calls=0;assert(d578_audio_apply(&p,emit,&s,&done)==-1 && s.calls==0);
    return 0;
}
