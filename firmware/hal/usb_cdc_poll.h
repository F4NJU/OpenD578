/* SPDX-License-Identifier: GPL-3.0-or-later */
#ifndef OPEND578_USB_CDC_POLL_H
#define OPEND578_USB_CDC_POLL_H
#include <stdint.h>
#include <stddef.h>
void d578_usb_init(void);
void d578_usb_poll(void);
size_t d578_usb_read(uint8_t *,size_t);
int d578_usb_write(const uint8_t *,size_t);
unsigned d578_usb_generation(void);
#endif
