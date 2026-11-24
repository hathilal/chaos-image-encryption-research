"""Host communication interface for the Zybo Chaos V8 FPGA firmware."""

import hashlib
import time

import serial


PIXELS = 128 * 128
BAUD_RATE = 115200
DEFAULT_PORT = "/dev/ttyUSB1"


def _wait_token(connection, token, timeout):
    deadline = time.monotonic() + timeout
    window = bytearray()

    while time.monotonic() < deadline:
        value = connection.read(1)
        if not value:
            continue

        window.extend(value)
        if len(window) > len(token):
            del window[:-len(token)]

        if bytes(window) == token:
            return

    raise TimeoutError(f"Timed out waiting for FPGA token {token!r}")


def _read_exact(connection, count, timeout):
    result = bytearray()
    deadline = time.monotonic() + timeout

    while len(result) < count:
        if time.monotonic() >= deadline:
            raise TimeoutError(
                f"FPGA returned {len(result)}/{count} output bytes"
            )

        chunk = connection.read(count - len(result))
        if chunk:
            result.extend(chunk)

    return bytes(result)


def transact(image_bytes, operation="encrypt",
             port=DEFAULT_PORT, baudrate=BAUD_RATE):
    """
    Send exactly one 128x128 grayscale image to V8.

    Protocol:
      Host -> FPGA: CHAO + operation byte + 16384 input bytes
      FPGA -> Host: RDY! + DONE + 16384 output bytes

    operation: 'encrypt' or 'decrypt'
    """

    payload = bytes(image_bytes)

    if len(payload) != PIXELS:
        raise ValueError(
            f"Expected exactly {PIXELS} bytes; received {len(payload)}"
        )

    operation_codes = {"encrypt": 0, "decrypt": 1}
    if operation not in operation_codes:
        raise ValueError("Operation must be 'encrypt' or 'decrypt'")

    code = operation_codes[operation]

    timings = {}
    total_start = time.perf_counter()

    with serial.Serial(
        port=port,
        baudrate=baudrate,
        timeout=0.25,
        write_timeout=15,
        bytesize=serial.EIGHTBITS,
        parity=serial.PARITY_NONE,
        stopbits=serial.STOPBITS_ONE,
    ) as connection:

        # Allow the serial connection to settle, then discard stale output.
        time.sleep(0.3)
        connection.reset_input_buffer()

        handshake_start = time.perf_counter()
        connection.write(b"CHAO" + bytes([code]))
        connection.flush()
        _wait_token(connection, b"RDY!", timeout=35)
        timings["handshake_seconds"] = (
            time.perf_counter() - handshake_start
        )

        transfer_start = time.perf_counter()
        written = connection.write(payload)
        connection.flush()

        if written != PIXELS:
            raise IOError(
                f"Serial write incomplete: {written}/{PIXELS} bytes"
            )

        timings["host_write_seconds"] = (
            time.perf_counter() - transfer_start
        )

        processing_start = time.perf_counter()
        _wait_token(connection, b"DONE", timeout=45)
        timings["wait_for_completion_seconds"] = (
            time.perf_counter() - processing_start
        )

        receive_start = time.perf_counter()
        output = _read_exact(connection, PIXELS, timeout=20)
        timings["host_read_seconds"] = (
            time.perf_counter() - receive_start
        )

    timings["round_trip_seconds"] = time.perf_counter() - total_start

    return {
        "operation": operation,
        "port": port,
        "baudrate": baudrate,
        "input_bytes": len(payload),
        "output_bytes": len(output),
        "input_sha256": hashlib.sha256(payload).hexdigest(),
        "output_sha256": hashlib.sha256(output).hexdigest(),
        "output": output,
        "timings": timings,
        "status": "SUCCESS",
    }
