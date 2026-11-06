/* D578 scheduler bridge. Counts every genuine Unicorn instruction; Python is
 * called at model deadlines and observation PCs. No instruction is replaced. */
#include <stdint.h>
typedef int (*reg_fn)(void *,int,void *);
typedef void (*notify_fn)(void *, uint64_t, uint32_t, void *);
typedef struct {
    uint64_t pending;
    uint64_t until;
    uint64_t address;
    uint32_t size;
    uint32_t start;
    uint32_t end;
    uint32_t app;
    unsigned char *traps;
    notify_fn notify;
    uint64_t calls;
    uint64_t instructions;
    uint32_t mask_tracking;
    reg_fn reg_read;
    uint32_t reg_basepri,reg_primask,reg_faultmask,mask_priority;
} gate;
#ifdef _WIN32
#define GATE_EXPORT __declspec(dllexport)
#else
#define GATE_EXPORT __attribute__((visibility("default")))
#endif
GATE_EXPORT void gate_code(void *uc,uint64_t address,uint32_t size,void *opaque) {
    gate *g=(gate *)opaque;
    g->pending++;g->instructions++;g->address=address;g->size=size;
    if (g->until)g->until--;
    unsigned mask_event=0;
    if (g->mask_tracking && address>=g->start && address<g->end && g->traps[(address-g->start)>>1]==2) {
        uint32_t basepri=0,primask=0,faultmask=0;
        g->reg_read(uc,(int)g->reg_basepri,&basepri);
        g->reg_read(uc,(int)g->reg_primask,&primask);
        g->reg_read(uc,(int)g->reg_faultmask,&faultmask);
        mask_event=!primask && !faultmask && (!basepri || g->mask_priority<basepri);
    }
    if (!g->until || address<g->start || address>=g->end ||
        (g->traps[(address-g->start)>>1]==1 ||
         mask_event)) {
        g->calls++;
        g->notify(uc,address,size,opaque);
    }
}
