/* Web monitor: compiles gemu-src's monitor.c unmodified (textual include)
 * and wraps gemu_monitor_poll() so that command lines queued from JavaScript
 * (see web_glue.c) are fed to the static monitor_handle_line() on the main
 * loop before each poll. This gives the browser the full GEMU console —
 * memory set/dump, breakpoints, reset, sendkey — with no stdin and no
 * threads. Monitor output goes to stdout, which Emscripten routes to
 * Module.print.
 *
 * This file replaces core/src/monitor.c in the web link; gemu-src itself is
 * never modified.
 */
#define gemu_monitor_poll gemu_web_real_monitor_poll
#include "monitor.c"
#undef gemu_monitor_poll

char *gemu_web_pop_line(void); /* web_glue.c */

GemuMonCmd gemu_monitor_poll(GemuMonitor *mon) {
    char *line;
    while ((line = gemu_web_pop_line()) != NULL) {
        char buf[512];
        snprintf(buf, sizeof buf, "%s", line);
        free(line);
        monitor_handle_line(mon, buf);
        fflush(stdout);
    }
    return gemu_web_real_monitor_poll(mon);
}
