# SPDX-FileCopyrightText: © 2024 Tiny Tapeout
# SPDX-License-Identifier: Apache-2.0

import cocotb
from cocotb.clock import Clock
from cocotb.triggers import ClockCycles


def pack_inputs(a, b):
    """Empaqueta dos números de 4 bits en un byte de 8 bits (a en altos, b en bajos)."""
    return ((a & 0xF) << 4) | (b & 0xF)


@cocotb.test()
async def test_project(dut):
    dut._log.info("Iniciando simulación de la ALU de 4 bits")

    # Configurar reloj a 100 KHz (periodo de 10 us)
    clock = Clock(dut.clk, 10, unit="us")
    cocotb.start_soon(clock.start())

    # Secuencia de Reset
    dut._log.info("Aplicando Reset")
    dut.ena.value = 1
    dut.ui_in.value = 0
    dut.uio_in.value = 0
    dut.rst_n.value = 0
    await ClockCycles(dut.clk, 10)
    dut.rst_n.value = 1
    await ClockCycles(dut.clk, 1)

    # Función auxiliar para enviar estímulos y esperar respuesta
    async def run_op(a, b, opcode):
        dut.ui_in.value = pack_inputs(a, b)
        dut.uio_in.value = opcode
        await ClockCycles(dut.clk, 2)
        res = int(dut.uo_out.value)
        uio = int(dut.uio_out.value)
        overflow = (uio >> 7) & 1
        carry_out = (uio >> 6) & 1
        return res, carry_out, overflow

    # 1. Prueba ADD (0000): 5 + 3 = 8 (Sin carry, sin overflow)
    res, carry, ovf = await run_op(5, 3, 0b0000)
    assert res == 8, f"ADD falló: esperado 8, obtenido {res}"
    assert carry == 0 and ovf == 0

    # 2. Prueba ADD con Carry y Overflow: 7 + 9 = 16 -> 0 en 4 bits, carry = 1
    res, carry, ovf = await run_op(7, 9, 0b0000)
    assert res == 0, f"ADD carry falló: esperado 0, obtenido {res}"
    assert carry == 1, f"ADD carry flag falló: esperado 1, obtenido {carry}"

    # 3. Prueba SUB (0001): 9 - 4 = 5
    res, carry, ovf = await run_op(9, 4, 0b0001)
    assert res == 5, f"SUB falló: esperado 5, obtenido {res}"

    # 4. Prueba MUL (0010): 6 * 7 = 42
    res, _, _ = await run_op(6, 7, 0b0010)
    assert res == 42, f"MUL falló: esperado 42, obtenido {res}"

    # 5. Prueba DIV (0011): 14 / 3 -> Cociente = 4, Residuo = 2 -> {residuo, cociente} = 0x24 (36)
    res, _, _ = await run_op(14, 3, 0b0011)
    assert res == 0x24, f"DIV falló: esperado 0x24, obtenido {hex(res)}"

    # 6. Prueba DIV por cero: 10 / 0 -> 0x00
    res, _, _ = await run_op(10, 0, 0b0011)
    assert res == 0, f"DIV por cero falló: esperado 0, obtenido {res}"

    # 7. Prueba AND (0100): 0b1100 (12) & 0b1010 (10) = 0b1000 (8)
    res, _, _ = await run_op(0b1100, 0b1010, 0b0100)
    assert res == 0b1000, f"AND falló: esperado 8, obtenido {res}"

    # 8. Prueba OR (0101): 0b1100 (12) | 0b1010 (10) = 0b1110 (14)
    res, _, _ = await run_op(0b1100, 0b1010, 0b0101)
    assert res == 0b1110, f"OR falló: esperado 14, obtenido {res}"

    # 9. Prueba XOR (0110): 0b1100 (12) ^ 0b1010 (10) = 0b0110 (6)
    res, _, _ = await run_op(0b1100, 0b1010, 0b0110)
    assert res == 0b0110, f"XOR falló: esperado 6, obtenido {res}"

    # 10. Prueba NOT (0111): ~0b0101 (5) = 0b1010 (10) en 4 bits
    res, _, _ = await run_op(0b0101, 0, 0b0111)
    assert res == 0b1010, f"NOT falló: esperado 10, obtenido {res}"

    # 11. Prueba ENC (1000): (a=0x3, b=0xC -> 0x3C) ^ 0xAB = 0x97
    res, _, _ = await run_op(0x3, 0xC, 0b1000)
    assert res == (0x3C ^ 0xAB), f"ENC falló: esperado {hex(0x3C ^ 0xAB)}, obtenido {hex(res)}"

    dut._log.info("¡Todas las pruebas de la ALU pasaron con éxito!")

