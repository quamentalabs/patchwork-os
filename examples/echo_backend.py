# SPDX-License-Identifier: Apache-2.0
"""A local byte-preserving echo process; no network or vendor CLI is used."""
import sys

sys.stdout.buffer.write(b"PATCHWORK_ECHO: " + sys.stdin.buffer.read())
sys.stdout.buffer.flush()
