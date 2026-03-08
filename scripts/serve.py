from __future__ import annotations

import argparse

import uvicorn

from controlled_docs.config import AppConfig
from controlled_docs.server import create_app


def main() -> None:
    parser = argparse.ArgumentParser(description="Serve the FastAPI app")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()

    config = AppConfig.from_env()
    app = create_app(config)
    uvicorn.run(app, host=args.host, port=args.port)


if __name__ == "__main__":
    main()

