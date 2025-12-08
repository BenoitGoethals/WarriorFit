import os

import aiohttp
from warriorfit.config.appliccation_config import ApplicationConfig
from warriorfit.data.repositories.abc_repository import ABCRepository
from warriorfit.utils.Os import Os
import aiofiles

class StatusApplicationController:
    async def status_db(self):
        repo = ABCRepository()
        status =  await repo.check_if_db_is_operational()
        if status:
            return "✅ OPERATIONAL"
        else:
            return "❌ DOWN"

    async def status_hr(self):
        url = ApplicationConfig().hr_url
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url) as response:
                    if response.status == 200:
                        return "✅ OPERATIONAL"
                    else:
                        return "❌ DOWN"
        except aiohttp.ClientError:
            return "❌ DOWN"

    async def status_server(self):
        project_root = Os.get_project_root()
        log = project_root / "logs" / "application.log"
        error = 0
        if log.exists():
            # Use aiofiles for async file operations

            async with aiofiles.open(log, "r") as f:
                lines = await f.readlines()
            error = sum(1 for line in lines if "error" in line.lower())
    
        return f"Log: {error} Errors"

    async def load_log_application(self)->str:
        project_root = Os.get_project_root()
        log_path = project_root / "logs" / "application.log"
        async with aiofiles.open(log_path, "r") as f:
            lines = await f.readlines()
            last_100_lines = lines[-100:] if len(lines) > 100 else lines
            return ''.join(last_100_lines)

    def check_log_modified(self):
        from warriorfit.utils.Os import Os
        project_root = Os.get_project_root()
        log_path = project_root / "logs" / "application.log"
        if log_path.exists():
            return os.path.getmtime(log_path)
        return None
        
        
