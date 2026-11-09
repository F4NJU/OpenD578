/* SPDX-License-Identifier: GPL-3.0-or-later */
#include "audio_control.h"

static bool valid(const d578_audio_context *c, d578_audio_plan *p)
{
    return c && p && (unsigned)c->speakers <= D578_BOTH_SPEAKERS &&
           (unsigned)c->path <= D578_PATH_SUB;
}
static d578_speakers mode(const d578_audio_context *c)
{
    return c->radio_override ? D578_RADIO_SPEAKER : c->speakers;
}
static d578_audio_plan start(uint16_t word)
{
    d578_audio_plan p = {0}; p.final_pio25=word; return p;
}
static void bit(d578_audio_plan *p, unsigned n, bool set, bool immediate)
{
    uint16_t mask=(uint16_t)(1u<<n);
    uint16_t next=set ? (uint16_t)(p->final_pio25|mask) : (uint16_t)(p->final_pio25&~mask);
    if(next!=p->final_pio25) {
        p->ops[p->count++]=(d578_audio_op){D578_RF_WRITE,1,0x25,next,immediate};
        p->final_pio25=next;
    }
}
bool d578_audio_enable(const d578_audio_context *c,uint16_t word,bool immediate,d578_audio_plan *out)
{
    if(!valid(c,out))return false;
    d578_audio_plan p=start(word);
    if(!c->output_hold) {
        d578_speakers m=mode(c);
        bit(&p,4,m==D578_RADIO_SPEAKER || c->special_mode,immediate);
        p.ops[p.count++]=(d578_audio_op){D578_GPIO_PA7,0,0,m==D578_MIC_SPEAKER, false};
    }
    *out=p;return true;
}
bool d578_audio_mute(uint16_t word,bool immediate,d578_audio_plan *out)
{
    if(!out)return false;
    d578_audio_plan p=start(word);bit(&p,4,true,immediate);
    p.ops[p.count++]=(d578_audio_op){D578_GPIO_PA7,0,0,1,false};
    *out=p;return true;
}
bool d578_audio_mic_path(const d578_audio_context *c,uint16_t word,bool immediate,d578_audio_plan *out)
{
    if(!valid(c,out))return false;
    d578_audio_plan p=start(word);
    if(c->aux_enabled && c->special_mode) {
        bit(&p,7,false,immediate);bit(&p,2,true,immediate);
    } else if(c->path==D578_PATH_MAIN) {
        bit(&p,7,true,immediate);bit(&p,2,false,immediate);
    } else {
        bit(&p,7,false,immediate);
        /* This routine reads the configured speaker mode directly, whereas
         * route_gate uses the getter with radio_override. */
        bit(&p,2,c->speakers==D578_BOTH_SPEAKERS && !c->sub_gate_hold,immediate);
    }
    *out=p;return true;
}
bool d578_audio_route_gate(const d578_audio_context *c,bool requested,uint16_t word,bool immediate,d578_audio_plan *out)
{
    if(!valid(c,out))return false;
    d578_audio_plan p=start(word);
    bit(&p,2,(mode(c)==D578_BOTH_SPEAKERS && c->path==D578_PATH_SUB) || requested,immediate);
    *out=p;return true;
}
bool d578_audio_aux_route(const d578_audio_context *c,bool requested,uint16_t word,bool immediate,d578_audio_plan *out)
{
    if(!valid(c,out))return false;
    d578_audio_plan p=start(word);
    if(c->aux_enabled && (c->special_mode || c->aux_active))
        bit(&p,7,!c->special_mode && requested,immediate);
    *out=p;return true;
}
bool d578_audio_fm_microphone(uint8_t level,uint8_t factory,d578_audio_plan *out)
{
    if(!out || level>5 || factory>63)return false;
    int delta=level==1?-2:(level==2 || level==3)?0:1;
    uint16_t applied=(uint16_t)((int)factory+delta);
    d578_audio_plan p=start(0);
    p.ops[0]=(d578_audio_op){D578_RF_WRITE,0,0x18,(uint16_t)(0x125u|((level+2u)<<11)),false};
    p.ops[1]=(d578_audio_op){D578_RF_WRITE,0,0x7f,1,false};
    p.ops[2]=(d578_audio_op){D578_RF_WRITE,0,0x17,(uint16_t)(0x200u|((uint32_t)applied<<3)),false};
    p.ops[3]=(d578_audio_op){D578_RF_WRITE,0,0x7f,0,false};p.count=4;
    *out=p;return true;
}
bool d578_audio_volume_level(uint16_t adc,uint8_t *out)
{
    if(!out || adc>4095)return false;
    *out=adc<=150?0:adc>=3936?32:(uint8_t)((adc-150)/124+1);return true;
}
bool d578_audio_volume_code(uint8_t level,uint8_t *out)
{
    /* Desired attenuation per user level, independently encoded as U2429 code. */
    static const uint8_t attenuation[33]={0,42,40,38,36,34,32,30,29,28,27,26,25,24,23,22,20,19,18,17,16,15,14,13,12,11,10,9,8,7,6,4,0};
    if(!out || level>32)return false;
    uint8_t db=attenuation[level];
    *out=level==0?0:(uint8_t)((21-db/4)|((3-db%4)<<5));return true;
}
int d578_audio_apply(const d578_audio_plan *p,d578_audio_emit emit,void *user,size_t *completed)
{
    if(completed)*completed=0;
    if(!p || !emit || p->count>4)return -1;
    for(size_t i=0;i<p->count;++i) {
        int result=emit(user,&p->ops[i]);
        if(result)return result;
        if(completed)*completed=i+1;
    }
    return 0;
}
