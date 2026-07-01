/* Browser glue for the web build.
 *
 * 1. Monitor input queue: JavaScript pushes GEMU console command lines via
 *    gemu_web_monitor_input(); the gemu_monitor_poll() wrapper in
 *    monitor_web.c drains them once per emulated frame, on the main loop.
 *    This replaces the native stdin-reading monitor thread (WASM builds are
 *    single-threaded; pthread_create fails gracefully and is never needed).
 *
 * 2. gemu_web_nanosleep(): machines pace themselves with nanosleep(), which
 *    busy-waits on the browser main thread. The whole build is compiled with
 *    -Dnanosleep=gemu_web_nanosleep so pacing goes through emscripten_sleep()
 *    (Asyncify) instead, yielding to the browser event loop each frame.
 */
#include <emscripten.h>
#include <stdlib.h>
#include <string.h>
#include <time.h>

#define WEB_MON_QUEUE 32

static char *mon_queue[WEB_MON_QUEUE];
static int   mon_head, mon_count;

EMSCRIPTEN_KEEPALIVE
void gemu_web_monitor_input(const char *line) {
    if (mon_count == WEB_MON_QUEUE)
        return; /* queue full — drop; the console is human-paced */
    mon_queue[(mon_head + mon_count) % WEB_MON_QUEUE] = strdup(line);
    mon_count++;
}

/* Pop one queued line, or NULL. Caller frees. */
char *gemu_web_pop_line(void) {
    if (!mon_count)
        return NULL;
    char *s = mon_queue[mon_head];
    mon_head = (mon_head + 1) % WEB_MON_QUEUE;
    mon_count--;
    return s;
}

int gemu_web_nanosleep(const struct timespec *req, struct timespec *rem) {
    (void)rem;
    double ms = (double)req->tv_sec * 1000.0 + (double)req->tv_nsec / 1e6;
    emscripten_sleep(ms < 0 ? 0 : (unsigned)ms);
    return 0;
}
