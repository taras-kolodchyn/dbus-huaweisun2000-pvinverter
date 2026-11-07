"""Run separately from pytest: unit-test collection installs pymodbus stubs."""

import importlib.metadata
from pathlib import Path
import socketserver
import struct
import sys
import threading
import unittest

sys.path.insert(0, str(Path(__file__).resolve().parents[2] / "src"))

from dbus_huaweisun2000_pvinverter.sun2000_modbus.inverter import (  # noqa: E402
    Sun2000,
    UnsupportedRegisterError,
)
from dbus_huaweisun2000_pvinverter.sun2000_modbus.registers import (  # noqa: E402
    InverterEquipmentRegister,
)

REGISTERS = {32069: 2300, 32080: 0, 32081: 5800}


class RegisterServer(socketserver.BaseRequestHandler):
    def receive(self, count):
        data = b""
        while len(data) < count:
            chunk = self.request.recv(count - len(data))
            if not chunk:
                return None
            data += chunk
        return data

    def handle(self):
        self.request.settimeout(5)
        while True:
            header = self.receive(7)
            if header is None:
                return
            transaction, protocol, length, unit = struct.unpack(">HHHB", header)
            payload = self.receive(length - 1)
            if payload is None:
                return
            function, address, count = struct.unpack(">BHH", payload)
            if protocol != 0 or unit != 7 or function != 3:
                response = bytes([function | 0x80, 3])
            elif any(address + i not in REGISTERS for i in range(count)):
                response = bytes([function | 0x80, 2])
            else:
                response = bytes([function, count * 2]) + b"".join(
                    struct.pack(">H", REGISTERS[address + i]) for i in range(count)
                )
            self.request.sendall(
                struct.pack(">HHHB", transaction, 0, len(response) + 1, unit) + response
            )


class RealPymodbusTest(unittest.TestCase):
    def test_driver_reads_and_handles_exceptions_over_real_tcp(self):
        with socketserver.ThreadingTCPServer(
            ("127.0.0.1", 0), RegisterServer
        ) as server:
            server.daemon_threads = True
            worker = threading.Thread(target=server.serve_forever, daemon=True)
            worker.start()
            driver = None
            try:
                driver = Sun2000(
                    host="127.0.0.1",
                    port=server.server_address[1],
                    modbus_unit=7,
                    wait=0,
                    timeout=2,
                    retries=1,
                )
                self.assertTrue(driver.connect())
                self.assertEqual(
                    driver.read(InverterEquipmentRegister.ActivePower), 5800
                )
                self.assertEqual(
                    driver.read(InverterEquipmentRegister.PhaseAVoltage), 230.0
                )
                self.assertEqual(
                    driver.read_range(32080, quantity=2), b"\x00\x00\x16\xa8"
                )
                with self.assertRaises(UnsupportedRegisterError):
                    driver.read_range(40562, quantity=2)
            finally:
                if driver is not None:
                    driver.disconnect()
                server.shutdown()
                worker.join(timeout=5)


if __name__ == "__main__":
    print(f"Testing real pymodbus {importlib.metadata.version('pymodbus')}", flush=True)
    unittest.main()
