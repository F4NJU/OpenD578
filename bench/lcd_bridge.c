/* Native dispatch of the same modeled D578 LCD GPIO edges. No ARM hook,
 * instruction replacement, manufacturer code, or controller drawing routine. */
#include <stdint.h>
#define CAPACITY 2048
#ifdef _WIN32
#define API __declspec(dllexport)
#else
#define API __attribute__((visibility("default")))
#endif

typedef uint64_t (*read_fn)(void *, uint64_t, unsigned, void *);
typedef void (*write_fn)(void *, uint64_t, unsigned, uint64_t, void *);
typedef void (*flush_fn)(void *);
typedef struct { uint64_t step; uint32_t value; uint32_t data; } edge;
typedef int (*reg_fn)(void *, int, void *);
typedef struct {
    uint64_t *instructions;
    uint64_t origin;
    uint64_t reads;
    uint64_t writes;
    uint32_t port_b;
    uint32_t port_e;
    uint32_t enabled;
    uint32_t count;
    read_fn slow_read;
    write_fn slow_write;
    flush_fn flush;
    edge edges[CAPACITY];
    reg_fn reg_read;
    uint32_t reg_r1;
    uint32_t reg_pc;
    uint32_t nand_enabled;
    uint32_t nand_bits;
    uint32_t nand_accumulator;
    uint32_t nand_input_count;
    uint32_t nand_clk;
    uint32_t nand_mosi;
    uint32_t nand_miso;
    uint32_t nand_io0;
    uint32_t cache_size;
    uint32_t cache_column;
    uint32_t seen_outputs;
    uint32_t flushed_outputs;
    unsigned char cache[2112];
    unsigned char input[2112];
} bridge;

API uint64_t lcd_bridge_read(void *uc, uint64_t offset, unsigned size, void *opaque) {
    bridge *b=(bridge *)opaque;
    if (b->enabled && size==4 && offset==0x180C) {
        b->reads++;
        return b->port_e;
    }
    if (b->enabled && b->nand_enabled && size==4 && (offset==0x808 || offset==0xC08)) {
        uint32_t mask=0,pc=0;
        b->reg_read(uc,(int)b->reg_r1,&mask);
        b->reg_read(uc,(int)b->reg_pc,&pc);
        if (pc==0x0800879A && ((offset==0x808 && mask==0x8000) || (offset==0xC08 && mask==0x4000))) {
            b->reads++;
            return offset==0x808 ? b->nand_miso<<15 : b->nand_io0<<14;
        }
    }
    return b->slow_read(uc,offset,size,opaque);
}

API void lcd_bridge_write(void *uc, uint64_t offset, unsigned size,
                          uint64_t value, void *opaque) {
    bridge *b=(bridge *)opaque;
    if (b->enabled && size==4) {
        uint32_t v=(uint32_t)value;
        if (offset==0x180C && !((b->port_e^v)&~UINT32_C(0x7F80))) {
            b->port_e=v;
            b->writes++;
            return;
        }
        if (offset==0xC10 || offset==0xC14) {
            uint32_t mask=offset==0xC10 ? (v|(v>>16))&0xFFFF : v;
            if (b->nand_enabled && !(mask&~UINT32_C(0xC000))) {
                uint32_t before=b->port_b;
                uint32_t after=offset==0xC10 ? (before|(v&0xFFFF))&~(v>>16) : before&~(v&0xFFFF);
                uint32_t clk=!!(after&0x8000),mosi=!!(after&0x4000);
                uint32_t byte_index=(b->nand_bits-32)*2/8;
                if ((mask&0x8000) && clk!=b->nand_clk && !clk && b->cache_column+byte_index>=b->cache_size) {
                    b->slow_write(uc,offset,size,value,opaque);
                    return;
                }
                if ((mask&0x8000) && clk!=b->nand_clk && clk && b->nand_bits%8==7 && b->nand_input_count>=2112) {
                    b->slow_write(uc,offset,size,value,opaque);
                    return;
                }
                b->port_b=after;
                if (mask&0x4000) b->nand_mosi=mosi;
                if ((mask&0x8000) && clk!=b->nand_clk) {
                    if (!clk) {
                        uint32_t bit=(b->nand_bits-32)*2%8;
                        uint32_t output=b->cache[b->cache_column+byte_index];
                        b->nand_miso=(output>>(7-bit))&1;
                        b->nand_io0=(output>>(6-bit))&1;
                        if (b->seen_outputs<byte_index+1) b->seen_outputs=byte_index+1;
                    } else {
                        b->nand_accumulator=(b->nand_accumulator<<1)|b->nand_mosi;
                        b->nand_bits++;
                        if (!(b->nand_bits%8)) {
                            b->input[b->nand_input_count++]=(unsigned char)b->nand_accumulator;
                            b->nand_accumulator=0;
                        }
                    }
                    b->nand_clk=clk;
                }
                b->writes++;
                return;
            }
            if (!(mask&~UINT32_C(0x2C00))) {
                uint32_t before=b->port_b;
                uint32_t after=offset==0xC10 ? (before|(v&0xFFFF))&~(v>>16) : before&~(v&0xFFFF);
                b->port_b=after;
                b->writes++;
                if (!(before&0x400) && (after&0x400) && !(after&0x2000)) {
                    unsigned index=b->count++;
                    b->edges[index].step=b->origin+*b->instructions;
                    b->edges[index].value=(b->port_e>>7)&255;
                    b->edges[index].data=!!(after&0x800);
                    if (b->count==CAPACITY) b->flush(opaque);
                }
                return;
            }
        }
    }
    b->slow_write(uc,offset,size,value,opaque);
}
