
import subprocess
import uuid
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import PlainTextResponse

app = FastAPI()

BOX_ROOT = Path("/var/lib/isolate")
MAX_SOURCE_BYTES = 64 * 1024


def command(args, timeout):
    return subprocess.run(
        args,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
        check=False,
    )


@app.get("/health")
def health():
    return {"status": "ok"}


@app.post("/run", response_class=PlainTextResponse)
async def run_cpp(request: Request):
    source = await request.body()

    if not source:
        raise HTTPException(400, "C++ source is required")
    if len(source) > MAX_SOURCE_BYTES:
        raise HTTPException(413, "Source too large")

    box_id = uuid.uuid4().int % 1_000

    try:
        init = command(
            ["isolate", "--box-id", str(box_id), "--init"],
            timeout=5,
        )
        if init.returncode != 0:
            raise HTTPException(500, "Could not initialize isolate")

        box = BOX_ROOT / str(box_id) / "box"
        (box / "main.cpp").write_bytes(source)

        compiled = command(
            [
                "isolate",
                "--box-id", str(box_id),
                "--time", "10",
                "--wall-time", "15",
                "--mem", "262144",
                "--fsize", "1024",
                "--processes=64",
                "--env=PATH",
                "--run", "--",
                "/usr/bin/g++", "-std=c++17", "-O2",
                "main.cpp", "-o", "main",
            ],
            timeout=20,
        )

        if compiled.returncode != 0:
            details = [
                f"Isolate exit code: {compiled.returncode}",
                compiled.stderr.decode("utf-8", errors="replace"),
                compiled.stdout.decode("utf-8", errors="replace"),
            ]

            for filename in ("stderr", "stdout"):
                output_file = box / filename
                if output_file.exists():
                    details.append(
                        f"{filename}:\n"
                        + output_file.read_text(errors="replace")
                    )

            raise HTTPException(
                status_code=400,
                detail="\n".join(item for item in details if item),
            )

        result = command(
            [
                "isolate",
                "--box-id", str(box_id),
                "--time", "5",
                "--wall-time", "8",
                "--mem", "262144",
                "--fsize", "1024",
                "--processes=64",
                "--env=PATH",
                "--run", "--", "./main",
            ],
            timeout=10,
        )

        return PlainTextResponse(
            result.stdout.decode("utf-8", errors="replace")
        )

    except subprocess.TimeoutExpired:
        raise HTTPException(408, "Execution timed out")
    finally:
        command(
            ["isolate", "--box-id", str(box_id), "--cleanup"],
            timeout=5,
        )
