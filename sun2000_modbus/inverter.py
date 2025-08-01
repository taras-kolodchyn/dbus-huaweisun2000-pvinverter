import logging
import time

from pymodbus.client.sync import ModbusTcpClient
from pymodbus.exceptions import ModbusIOException, ConnectionException

from . import datatypes

logging.basicConfig(level=logging.INFO)


class Sun2000:
    def __init__(
        self,
        host,
        port=502,
        timeout=5,
        wait=2,
        modbus_unit=3,
        retries=3,
        retry_delay=1,
    ):
        # 'retries' - number of attempts to read a register in case of errors
        # 'retry_delay' - delay in seconds between retry attempts
        self.wait = wait
        self.modbus_unit = modbus_unit
        self.inverter = ModbusTcpClient(
            host,
            port,
            timeout=timeout,
        )
        self.retries = retries
        self.retry_delay = retry_delay

    def connect(self):
        if not self.isConnected():
            self.inverter.connect()
            time.sleep(self.wait)
            if self.isConnected():
                logging.info("Successfully connected to inverter")
                return True
            else:
                logging.error("Connection to inverter failed")
                return False
        else:
            return True

    def disconnect(self):
        """Close the underlying tcp socket"""
        # Some Sun2000 models with the SDongle WLAN-FE
        # require the TCP connection to be closed
        # as soon as possible.
        # Leaving the TCP connection open for an extended time may cause
        # dongle reboots and/or FusionSolar portal
        # updates to be delayed or even paused.
        self.inverter.close()

    def isConnected(self):
        """Check if underlying tcp socket is open"""
        return self.inverter.is_socket_open()

    def read_raw_value(self, register):
        # Try to read the register value
        # with several retries in case of communication errors
        if not self.isConnected():
            raise ValueError("Inverter is not connected")

        attempt = 0
        last_exception = None
        while attempt < self.retries:
            try:
                register_value = self.inverter.read_holding_registers(
                    register.value.address,
                    register.value.quantity,
                    unit=self.modbus_unit,
                )
                if isinstance(register_value, ModbusIOException):
                    logging.error("Inverter modbus unit did not respond")
                    raise register_value
                # If successful, decode and return the value
                return datatypes.decode(
                    register_value.encode()[1:],
                    register.value.data_type,
                )
            except (ConnectionException, ModbusIOException) as ex:
                last_exception = ex
                logging.error(f"Read attempt {attempt + 1} failed: " f"{ex}")
                time.sleep(self.retry_delay)
                # Try to reconnect before next attempt
                try:
                    self.disconnect()
                except Exception as disconnect_ex:
                    logging.warning(f"Error while disconnecting: {disconnect_ex}")
                try:
                    self.connect()
                except Exception as connect_ex:
                    logging.warning(f"Error while reconnecting: {connect_ex}")
            attempt += 1
        # All retries failed, raise the last exception
        logging.critical("All retries to read register failed")
        raise (
            last_exception
            if last_exception
            else Exception("Unknown error during register read")
        )

    def read(self, register):
        raw_value = self.read_raw_value(register)

        if register.value.gain is None:
            return raw_value
        else:
            return raw_value / register.value.gain

    def read_formatted(self, register):
        value = self.read(register)

        if register.value.unit is not None:
            return f"{value} {register.value.unit}"
        elif register.value.mapping is not None:
            return register.value.mapping.get(value, "undefined")
        else:
            return value

    def read_range(self, start_address, quantity=0, end_address=0):
        # Try to read a range of registers with retries
        if quantity == 0 and end_address == 0:
            raise ValueError(
                "Either parameter quantity or end_address is required and must be "
                "greater than 0"
            )
        if quantity != 0 and end_address != 0:
            raise ValueError(
                "Only one parameter quantity or end_address should be defined"
            )
        if end_address != 0 and end_address <= start_address:
            raise ValueError("end_address must be greater than start_address")

        if not self.isConnected():
            raise ValueError("Inverter is not connected")

        if end_address != 0:
            quantity = end_address - start_address + 1

        attempt = 0
        last_exception = None
        while attempt < self.retries:
            try:
                register_range_value = self.inverter.read_holding_registers(
                    start_address,
                    quantity,
                    unit=self.modbus_unit,
                )
                if isinstance(register_range_value, ModbusIOException):
                    logging.error("Inverter modbus unit did not respond")
                    raise register_range_value
                # If successful, decode and return the value
                return datatypes.decode(
                    register_range_value.encode()[1:],
                    datatypes.DataType.MULTIDATA,
                )
            except (ConnectionException, ModbusIOException) as ex:
                last_exception = ex
                logging.error(f"Range read attempt {attempt + 1} failed: " f"{ex}")
                time.sleep(self.retry_delay)
                # Try to reconnect before next attempt
                try:
                    self.disconnect()
                except Exception as disconnect_ex:
                    logging.warning(f"Error while disconnecting: {disconnect_ex}")
                try:
                    self.connect()
                except Exception as connect_ex:
                    logging.warning(f"Error while reconnecting: {connect_ex}")
            attempt += 1
        # All retries failed, raise the last exception
        logging.critical("All retries to read range of registers failed")
        raise (
            last_exception
            if last_exception
            else Exception("Unknown error during register range read")
        )
