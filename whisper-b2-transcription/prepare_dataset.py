"""Stage the demo audio file used by ``whisper_b2_transcription.ipynb`` in a
Backblaze B2 bucket.

The notebook expects ``s3://b2datasets/whisper-demo/jfk.flac`` to exist and be
anonymously readable. ``jfk.flac`` is the ~10 second clip that ships with the
openai/whisper repo (public domain US government recording) and is the
canonical Whisper smoke-test asset.

Usage::

    python prepare_dataset.py --download-only --out ./jfk.flac

    python prepare_dataset.py --bucket b2datasets --prefix whisper-demo
"""

from __future__ import annotations

import argparse
import os
import shutil
import sys
import urllib.request
from pathlib import Path

SOURCE_URL = "https://github.com/openai/whisper/raw/main/tests/jfk.flac"
DEFAULT_FILENAME = "jfk.flac"


def download(out_path: Path) -> Path:
    out_path.parent.mkdir(parents=True, exist_ok=True)
    print(f"Downloading {SOURCE_URL} -> {out_path}")
    with urllib.request.urlopen(SOURCE_URL) as resp, out_path.open("wb") as fh:
        shutil.copyfileobj(resp, fh)
    print(f"  wrote {out_path.stat().st_size:,} bytes")
    return out_path


def upload(local_path: Path, bucket: str, key: str, endpoint_url: str) -> None:
    try:
        import boto3
    except ImportError:
        sys.exit("boto3 is required for upload; pip install boto3")
    client = boto3.client(
        "s3",
        endpoint_url=endpoint_url,
        aws_access_key_id=os.environ.get("AWS_ACCESS_KEY_ID")
        or os.environ.get("B2_APPLICATION_KEY_ID"),
        aws_secret_access_key=os.environ.get("AWS_SECRET_ACCESS_KEY")
        or os.environ.get("B2_APPLICATION_KEY"),
    )
    print(f"Uploading -> s3://{bucket}/{key}")
    client.upload_file(str(local_path), bucket, key)
    print("  done")


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__.split("\n", 1)[0])
    parser.add_argument("--bucket", default="b2datasets")
    parser.add_argument("--prefix", default="whisper-demo")
    parser.add_argument(
        "--endpoint-url",
        default="https://s3.us-west-001.backblazeb2.com",
        help="B2 S3 endpoint URL (default: us-west-001, where b2datasets lives)",
    )
    parser.add_argument("--out", default=DEFAULT_FILENAME)
    parser.add_argument(
        "--download-only",
        action="store_true",
        help="Skip upload; only download the audio locally.",
    )
    args = parser.parse_args()

    local = Path(args.out)
    download(local)
    if args.download_only:
        return
    upload(local, args.bucket, f"{args.prefix}/{DEFAULT_FILENAME}", args.endpoint_url)


if __name__ == "__main__":
    main()
