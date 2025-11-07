
import logging
import asyncio
from typing import List, Tuple, Tuple

logger = logging.getLogger(__name__)

class UplinkMonitor:
    def __init__(self, restore_connection_cmd: List[str], check_connection_cmd: List[str], check_interval_s: int):
        self.restore_connection_cmd = restore_connection_cmd
        self.check_connection_cmd = check_connection_cmd
        self.check_interval_s = check_interval_s
        self.connection_up = False

    async def run(self):
        while True:
            # Monitoring logic here
            await asyncio.sleep(self.check_interval_s)

    async def check_connection(self) -> bool:
        ret_code, stdout, stderr = await self._run_command(self.check_connection_cmd)

        if ret_code == 0:
            logger.info("Connection is up.")
            return True
        else:
            logger.error("Connection is down.")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False

    async def restore_connection(self) -> bool:
        ret_code, stdout, stderr = await self._run_command(self.restore_connection_cmd)

        if ret_code == 0:
            logger.info("Connection restored successfully.")
            return True
        else:
            logger.error(f"Failed to restore connection")
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False

    async def _run_command(self, command: List[str]) -> Tuple[int, str, str]:
        proc = await asyncio.create_subprocess_exec(
            *command,
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.PIPE
        )
        stdout, stderr = await proc.communicate()
        stdout = stdout.decode() if stdout else ''
        stderr = stderr.decode() if stderr else ''
        return proc.returncode, stdout, stderr
