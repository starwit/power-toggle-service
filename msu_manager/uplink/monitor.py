
import logging
import asyncio
from typing import List, Tuple, Tuple

logger = logging.getLogger(__name__)

class UplinkMonitor:
    def __init__(self, restore_connection_cmd: List[str], check_connection_target: str, check_interval_s: int):
        self.restore_connection_cmd = restore_connection_cmd
        self.check_connection_cmd = ['ping', '-c', '1', '-W', '0.5', check_connection_target]
        self.check_interval_s = check_interval_s

    async def run(self):
        try:
            while True:
                is_up = await self.check_connection()
                logger.debug(f'Connection status: {"up" if is_up else "down"}')
                if not is_up:
                    logger.warning("Connection is down, attempting to restore...")
                    success = await self.restore_connection()
                    if success:
                        logger.info("Connection restored successfully.")
                    else:
                        logger.error("Failed to restore connection.")
                await asyncio.sleep(self.check_interval_s)
        except asyncio.CancelledError:
            logger.info("UplinkMonitor task cancelled.")
            raise
        except Exception as e:
            logger.error(f"Unexpected error occurred in UplinkMonitor", exc_info=True)

    async def check_connection(self) -> bool:
        ret_code, stdout, stderr = await self._run_command(self.check_connection_cmd)

        if ret_code == 0:
            return True
        else:
            logger.error(f'Connection check failed. Output of {" ".join(self.check_connection_cmd)}')
            logger.error(f"STDOUT: {stdout}")
            logger.error(f"STDERR: {stderr}")
            return False

    async def restore_connection(self) -> bool:
        ret_code, stdout, stderr = await self._run_command(self.restore_connection_cmd)

        if ret_code == 0:
            return True
        else:
            logger.error(f"Failed to restore connection. Output of {' '.join(self.restore_connection_cmd)}")
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
