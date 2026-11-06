"""Identify the running web bench before reusing its local server."""
import hashlib
from pathlib import Path

VERSION = 'V11.7'
APPLICATION = 'D578 local bench ' + VERSION
BUILD_FILES = ('bench_version.py', 'web_launcher.py', 'web_server.py',
               'prepare_inputs.py', 'run_lcd.py', 'web/index.html',
               'web/app.js', 'web/style.css', 'native_gate.py',
               'interactive_runtime.py', 'board_clock.py', 'emulate_front_v121.py',
               'emulate_lcd_v121.py', 'bench_runner.py', 'lab_runner.py',
               'lcd_bridge.py', 'lcd_bridge.c', 'lcd_bus.py',
               'native_gate.c', 'cortex_exceptions.py', 'ensure_environment.py',
               'hardware_runner.py', 'run_hardware.py', 'board_image.py',
               'usbd_host.py', 'watchdog.py', 'sct_hpi.py',
               'execution_coverage.py', 'firmware_inventory.py', 'audio_iq.py',
               'ax25_afsk.py', 'web/audio_lab.js', 'web/audio_capture_worklet.js',
               'usb_cdc.py', 'usb_cdc_runtime.py', 'cps_bridge.py', 'cps_probe.py', 'nand_state.py', 'web/cps_link.js', 'web_endpoint.py', 'cdc_channel.py', 'web/mini_cps_protocol.js', 'web/mini_cps.js', 'web/qualification.js', 'board_observations.py', 'status_led.py', 'ready_session.py',
               'qualification_data/catalog.json')


def build_id(root):
    digest = hashlib.sha256()
    for name in BUILD_FILES:
        digest.update(name.encode('utf-8') + b'\0')
        digest.update((Path(root) / name).read_bytes())
    return digest.hexdigest()


def server_matches(config, root_id, expected_build):
    return (isinstance(config, dict) and config.get('root_id') == root_id
            and config.get('application') == APPLICATION
            and config.get('build_id') == expected_build)
