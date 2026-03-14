import os
import datetime
from pathlib import Path

class Logger:
    def __init__(self, log_dir="logs", feature="session"):
        self.log_dir = Path(log_dir)
        self.log_dir.mkdir(parents=True, exist_ok=True)
        now = datetime.datetime.now()
        filename = now.strftime(f"%d-%m-%y_%H%M_{feature}.md")
        self.log_path = self.log_dir / filename

        # Init file
        with open(self.log_path, "w") as f:
            f.write(f"# Session Log: {feature}\n")
            f.write(f"Started at: {now.isoformat()}\n\n")

    def _write(self, level: str, msg: str):
        time_str = datetime.datetime.now().strftime("%H:%M:%S.%f")[:-3]
        line = f"- **[{time_str}] [{level}]** {msg}\n"
        with open(self.log_path, "a") as f:
            f.write(line)
        print(line.strip())

    def info(self, msg: str):
        self._write("INFO", msg)

    def event(self, msg: str):
        self._write("EVENT", msg)

    def memory(self, msg: str):
        self._write("MEMORY", msg)

    def parse(self, msg: str):
        self._write("PARSE", msg)

    def state(self, msg: str):
        self._write("STATE", msg)

    def warn(self, msg: str):
        self._write("WARN", msg)

    def error(self, msg: str):
        self._write("ERROR", msg)
