import logging
import time

try:
    from pymodbus.client import ModbusTcpClient
except ImportError:  # pragma: no cover - legacy pymodbus 2.x
    from pymodbus.client.sync import ModbusTcpClient

try:
    from pymodbus.exceptions import ModbusIOException, ConnectionException
except ImportError:  # pragma: no cover - legacy pymodbus 2.x names
    from pymodbus.exceptions import ModbusIOException  # type: ignore

    class ConnectionException(ModbusIOException):
        pass


from .. import config
from . import datatypes

LOG = logging.getLogger(__name__)


class ModbusResponseError(ModbusIOException):
    def __init__(self, address, quantity, response):
        end_address = address + quantity - 1
        self.address = address
        self.quantity = quantity
        self.end_address = end_address
        self.response = response
        self.function_code = getattr(response, "function_code", None)
        self.exception_code = getattr(
            response,
            "exception_code",
            getattr(response, "exceptionCode", None),
        )
        super().__init__(
            "Modbus exception response while reading "
            f"{address}-{end_address}: {response}"
        )


class UnsupportedRegisterError(ModbusResponseError):
    pass


def _raise_on_error_response(response, address, quantity):
    if isinstance(response, ModbusIOException):
        LOG.error("Inverter modbus unit did not respond")
        raise response

    if hasattr(response, "isError") and response.isError():
        exception_code = getattr(
            response,
            "exception_code",
            getattr(response, "exceptionCode", None),
        )
        if exception_code == 2:
            raise UnsupportedRegisterError(address, quantity, response)
        raise ModbusResponseError(address, quantity, response)


class Sun2000:
    def __init__(
        self,
        host,
        port=config.DEFAULT_MODBUS_PORT,
        timeout=5,
        wait=2,
        modbus_unit=config.DEFAULT_MODBUS_UNIT,
        retries=3,
        retry_delay=1,
    ):
        # 'retries' - number of attempts to read a register in case of errors
        # 'retry_delay' - delay in seconds between retry attempts
        self._connect_timeout = max(wait, 0)
        self._connect_poll_interval = 0.1
        self._post_connect_delay = max(wait, 0)
        self.modbus_unit = modbus_unit
        self.inverter = ModbusTcpClient(
            host,
            port,
            timeout=timeout,
        )
        self.retries = retries
        self.retry_delay = retry_delay
        self._host = host
        self._port = port

    @staticmethod
    def _is_fast_retry_error(error):
        message = str(error)
        return (
            "Connection unexpectedly closed" in message
            or "No Response received from the remote unit" in message
            or "Unable to decode response" in message
        )

    def connect(self, post_connect_delay=None):
        if self.isConnected():
            return True

        effective_post_connect_delay = (
            self._post_connect_delay
            if post_connect_delay is None
            else max(float(post_connect_delay), 0.0)
        )
        self.inverter.connect()
        deadline = time.monotonic() + max(self._connect_timeout, 0)
        while not self.isConnected() and time.monotonic() < deadline:
            time.sleep(self._connect_poll_interval)

        if self.isConnected():
            if effective_post_connect_delay:
                time.sleep(effective_post_connect_delay)
            LOG.info("Successfully connected to inverter %s:%s", self._host, self._port)
            return True

        LOG.error(
            "Connection to inverter %s:%s failed after %.1fs",
            self._host,
            self._port,
            self._connect_timeout,
        )
        return False

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

    def _resolve_retry_policy(self, retries=None, retry_delay=None):
        effective_retries = self.retries if retries is None else retries
        effective_retry_delay = self.retry_delay if retry_delay is None else retry_delay
        return max(int(effective_retries), 1), max(float(effective_retry_delay), 0.0)

    def _reconnect_for_retry(self, *, fast=False):
        try:
            self.disconnect()
        except Exception as disconnect_ex:
            LOG.warning("Error while disconnecting: %s", disconnect_ex)
        try:
            self.connect(post_connect_delay=0 if fast else None)
        except Exception as connect_ex:
            LOG.warning("Error while reconnecting: %s", connect_ex)

    def read_raw_value(self, register, retries=None, retry_delay=None):
        # Try to read the register value
        # with several retries in case of communication errors
        if not self.isConnected():
            raise ValueError("Inverter is not connected")

        effective_retries, effective_retry_delay = self._resolve_retry_policy(
            retries=retries,
            retry_delay=retry_delay,
        )
        attempt = 0
        last_exception = None
        while attempt < effective_retries:
            try:
                register_value = self.inverter.read_holding_registers(
                    register.value.address,
                    register.value.quantity,
                    unit=self.modbus_unit,
                )
                _raise_on_error_response(
                    register_value,
                    register.value.address,
                    register.value.quantity,
                )
                # If successful, decode and return the value
                return datatypes.decode(
                    register_value.encode()[1:],
                    register.value.data_type,
                )
            except UnsupportedRegisterError:
                raise
            except (ConnectionException, ModbusIOException) as ex:
                last_exception = ex
                LOG.error("Read attempt %d failed: %s", attempt + 1, ex)
                attempt += 1
                if attempt >= effective_retries:
                    break
                fast_retry = attempt == 1 and self._is_fast_retry_error(ex)
                if fast_retry:
                    LOG.debug(
                        "Fast retrying register %s after transport error",
                        register.value.address,
                    )
                elif effective_retry_delay:
                    time.sleep(effective_retry_delay)
                self._reconnect_for_retry(fast=fast_retry)
        # All retries failed, raise the last exception
        LOG.critical("All retries to read register failed")
        raise (
            last_exception
            if last_exception
            else Exception("Unknown error during register read")
        )

    def read(self, register, retries=None, retry_delay=None):
        raw_value = self.read_raw_value(
            register,
            retries=retries,
            retry_delay=retry_delay,
        )

        if register.value.gain is None:
            return raw_value
        else:
            return raw_value / register.value.gain

    def read_formatted(self, register, retries=None, retry_delay=None):
        value = self.read(
            register,
            retries=retries,
            retry_delay=retry_delay,
        )

        if register.value.unit is not None:
            return f"{value} {register.value.unit}"
        elif register.value.mapping is not None:
            return register.value.mapping.get(value, "undefined")
        else:
            return value

    def read_range(
        self,
        start_address,
        quantity=0,
        end_address=0,
        retries=None,
        retry_delay=None,
    ):
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

        effective_retries, effective_retry_delay = self._resolve_retry_policy(
            retries=retries,
            retry_delay=retry_delay,
        )
        attempt = 0
        last_exception = None
        while attempt < effective_retries:
            try:
                register_range_value = self.inverter.read_holding_registers(
                    start_address,
                    quantity,
                    unit=self.modbus_unit,
                )
                _raise_on_error_response(register_range_value, start_address, quantity)
                # If successful, decode and return the value
                return datatypes.decode(
                    register_range_value.encode()[1:],
                    datatypes.DataType.MULTIDATA,
                )
            except UnsupportedRegisterError:
                raise
            except (ConnectionException, ModbusIOException) as ex:
                last_exception = ex
                LOG.error("Range read attempt %d failed: %s", attempt + 1, ex)
                attempt += 1
                if attempt >= effective_retries:
                    break
                fast_retry = attempt == 1 and self._is_fast_retry_error(ex)
                if fast_retry:
                    LOG.debug(
                        "Fast retrying range %s-%s after transport error",
                        start_address,
                        start_address + quantity - 1,
                    )
                elif effective_retry_delay:
                    time.sleep(effective_retry_delay)
                self._reconnect_for_retry(fast=fast_retry)
        # All retries failed, raise the last exception
        LOG.critical("All retries to read range of registers failed")
        raise (
            last_exception
            if last_exception
            else Exception("Unknown error during register range read")
        )
