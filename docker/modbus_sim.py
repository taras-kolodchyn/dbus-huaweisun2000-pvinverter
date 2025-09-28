import logging
import os

from pymodbus.datastore import ModbusServerContext, ModbusSlaveContext
from pymodbus.datastore import ModbusSequentialDataBlock
from pymodbus.server.sync import StartTcpServer

logging.basicConfig(level=logging.INFO)

PORT = int(os.getenv("MODBUS_SIM_PORT", "15020"))
UNIT_ID = int(os.getenv("MODBUS_SIM_UNIT", "1"))


def encode_u16(value):
    return value & 0xFFFF


def encode_s32(value):
    if value < 0:
        value = (1 << 32) + value
    return [(value >> 16) & 0xFFFF, value & 0xFFFF]


def encode_u32(value):
    return [(value >> 16) & 0xFFFF, value & 0xFFFF]


block = ModbusSequentialDataBlock(0, [0] * 40000)

block.setValues(32069, [encode_u16(2300)])
block.setValues(32070, [encode_u16(2310)])
block.setValues(32071, [encode_u16(2290)])
block.setValues(32072, encode_s32(12000))
block.setValues(32074, encode_s32(11800))
block.setValues(32076, encode_s32(11500))
block.setValues(32080, encode_s32(5800))
block.setValues(32084, [encode_u16(950)])
block.setValues(32085, [encode_u16(5000)])
block.setValues(32106, encode_u32(123450))
block.setValues(30075, encode_u32(10000))
block.setValues(32064, encode_s32(6200))

store = ModbusSlaveContext(hr=block, zero_mode=True)
context = ModbusServerContext(slaves={UNIT_ID: store}, single=False)

logging.info("Starting Modbus simulator on 0.0.0.0:%s (unit %s)", PORT, UNIT_ID)
StartTcpServer(context, address=("0.0.0.0", PORT))
