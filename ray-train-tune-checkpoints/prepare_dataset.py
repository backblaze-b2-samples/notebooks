"""Generate the California Housing parquet files used by ``ray_train_b2.ipynb``.

Run this once to produce ``train.parquet`` and ``test.parquet``, then upload
the resulting directory to a public Backblaze B2 bucket. The notebook reads
from ``b2datasets/ray-train-demo/california_housing/`` by default, but the
layout works against any S3-compatible bucket.

Usage
-----

1. Install dependencies (one-off)::

    pip install scikit-learn pandas pyarrow

2. Generate the parquet files::

    python prepare_dataset.py --out ./california_housing

3. Upload to your public B2 bucket. With the AWS CLI (after ``pip install awscli``)::

    aws s3 sync ./california_housing/ \\
        s3://b2datasets/ray-train-demo/california_housing/ \\
        --endpoint-url https://s3.us-west-001.backblazeb2.com

   Or with the native Backblaze ``b2`` CLI::

    b2 sync ./california_housing/ b2://b2datasets/ray-train-demo/california_housing/

The resulting layout is::

    b2datasets/
    └── ray-train-demo/
        └── california_housing/
            ├── train.parquet
            └── test.parquet

The bucket must be set to ``Public`` in the B2 console for the notebook's
anonymous-read code path (``S3FileSystem(anonymous=True)``) to work.
"""

import argparse
from pathlib import Path

import pandas as pd
from sklearn.datasets import fetch_california_housing
from sklearn.model_selection import train_test_split


def main() -> None:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--out",
        type=Path,
        default=Path("california_housing"),
        help="Output directory for train.parquet / test.parquet",
    )
    parser.add_argument(
        "--test-size",
        type=float,
        default=0.2,
        help="Test split fraction (default: 0.2)",
    )
    parser.add_argument(
        "--seed",
        type=int,
        default=42,
        help="Random seed for the train/test split (default: 42)",
    )
    args = parser.parse_args()

    # Fetch California Housing, bundled with scikit-learn, public domain.
    bunch = fetch_california_housing(as_frame=True)
    df: pd.DataFrame = bunch.frame  # has features + MedHouseVal target column

    train_df, test_df = train_test_split(
        df, test_size=args.test_size, random_state=args.seed
    )

    args.out.mkdir(parents=True, exist_ok=True)
    train_path = args.out / "train.parquet"
    test_path = args.out / "test.parquet"

    train_df.to_parquet(train_path, index=False)
    test_df.to_parquet(test_path, index=False)

    print(f"Wrote {len(train_df):>6d} rows to {train_path}")
    print(f"Wrote {len(test_df):>6d} rows to {test_path}")


if __name__ == "__main__":
    main()
