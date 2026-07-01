/* VNC stub for the web build.
 *
 * The native VNC server needs BSD sockets and OpenSSL DES, neither of which
 * makes sense in a browser — the display *is* the local canvas. All entry
 * points are no-ops; gemu_vnc_create() returns NULL, which every caller in
 * gemu-src already treats as "VNC disabled".
 */
#include "gemu/vnc.h"
#include <stdio.h>
#include <string.h>

GemuVncServer *gemu_vnc_create(const char *addr, int fb_w, int fb_h) {
    (void)fb_w; (void)fb_h;
    if (addr)
        fprintf(stderr, "gemu: VNC is not available in the web build\n");
    return NULL;
}

void gemu_vnc_destroy(GemuVncServer *vnc) { (void)vnc; }

void gemu_vnc_set_password(GemuVncServer *vnc, const char *password) {
    (void)vnc; (void)password;
}

void gemu_vnc_set_colors(GemuVncServer *vnc, uint32_t fg_rgb, uint32_t bg_rgb) {
    (void)vnc; (void)fg_rgb; (void)bg_rgb;
}

void gemu_vnc_set_palette(GemuVncServer *vnc, const uint32_t *palette,
                          int n_colors) {
    (void)vnc; (void)palette; (void)n_colors;
}

void gemu_vnc_update(GemuVncServer *vnc, const uint8_t *vram, int vw, int vh) {
    (void)vnc; (void)vram; (void)vw; (void)vh;
}

void gemu_vnc_get_keys(GemuVncServer *vnc, uint8_t keys[16]) {
    (void)vnc;
    memset(keys, 0, 16);
}

uint32_t gemu_vnc_pop_keysym(GemuVncServer *vnc) {
    (void)vnc;
    return 0;
}

bool gemu_vnc_pop_key_event(GemuVncServer *vnc, GemuVncKeyEvent *event) {
    (void)vnc; (void)event;
    return false;
}
