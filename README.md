# Backblaze B2 sample notebooks

Example notebooks demonstrating how to use [Backblaze B2 Cloud Storage](https://www.backblaze.com/cloud-storage)
with AI and data workflows. Each subdirectory is a self-contained example with its own
`README.md`, dependencies, and runnable notebook.

## Contents

- [Backblaze B2 sample notebooks](#backblaze-b2-sample-notebooks)
  - [Contents](#contents)
  - [Examples](#examples)
    - [`image-classification-pytorch/`](#image-classification-pytorch)
    - [`ray-train-tune-checkpoints/`](#ray-train-tune-checkpoints)
    - [`whisper-b2-transcription/`](#whisper-b2-transcription)
    - [`lakefs-b2-dataset-versioning/`](#lakefs-b2-dataset-versioning)
  - [How to run an example](#how-to-run-an-example)
  - [Backblaze B2 prerequisites](#backblaze-b2-prerequisites)
  - [Contributing](#contributing)
  - [Related](#related)

## Examples

### [`image-classification-pytorch/`](./image-classification-pytorch/)

Train a PyTorch CIFAR-10 image classifier on data hosted in Backblaze B2. Demonstrates
a custom PyTorch `Dataset` that streams training images from a B2 bucket via the
S3-compatible API, learning to recognize the 10 CIFAR-10 categories
(airplanes, cars, birds, cats, deer, dogs, frogs, horses, ships, trucks).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1cOjN8ySp6wj_i6ZlH8qulRTCV8japlHN#scrollTo=74dOjOK6CEAD) [![Open In Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/backblaze-b2-samples/notebooks/HEAD?urlpath=lab/tree/image-classification-pytorch/cifar10_b2_pytorch_training.ipynb) [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/backblaze-b2-samples/notebooks?quickstart=1)

### [`ray-train-tune-checkpoints/`](./ray-train-tune-checkpoints/)

End-to-end [Ray Train](https://docs.ray.io/en/latest/train/train.html) +
[Ray Tune](https://docs.ray.io/en/latest/tune/index.html) example with checkpoints on
Backblaze B2. Reads California Housing parquet from a public B2 bucket, trains a small
PyTorch regression model with `TorchTrainer`, writes checkpoints back to a private B2
bucket via `RunConfig(storage_path="s3://...")`, and runs an optional `Tuner` sweep over
learning rates. Companion to the [Ray Train persistent-storage user guide](https://docs.ray.io/en/master/train/user-guides/persistent-storage.html#s3-compatible-storage-minio-backblaze-b2-etc).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/backblaze-b2-samples/notebooks/blob/main/ray-train-tune-checkpoints/ray_train_b2.ipynb) [![Open In Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/backblaze-b2-samples/notebooks/HEAD?urlpath=lab/tree/ray-train-tune-checkpoints/ray_train_b2.ipynb) [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/backblaze-b2-samples/notebooks?quickstart=1)

### [`whisper-b2-transcription/`](./whisper-b2-transcription/)

Speech-to-text transcription on Backblaze B2 with [OpenAI Whisper](https://github.com/openai/whisper).
Streams a public-domain demo audio clip (`jfk.flac`) from a public B2 bucket via
the S3-compatible API, runs Whisper for ASR, and optionally writes the
transcript JSON back to a private B2 bucket. Starting point for batch
transcription pipelines on B2-hosted audio archives.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/backblaze-b2-samples/notebooks/blob/main/whisper-b2-transcription/whisper_b2_transcription.ipynb) [![Open In Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/backblaze-b2-samples/notebooks/HEAD?urlpath=lab/tree/whisper-b2-transcription/whisper_b2_transcription.ipynb) [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/backblaze-b2-samples/notebooks?quickstart=1)

### [`lakefs-b2-dataset-versioning/`](./lakefs-b2-dataset-versioning/)

Branch-per-experiment dataset versioning for ML with [lakeFS](https://lakefs.io) on top of
Backblaze B2. Walks a satellite-imagery scenario: ingest a tile catalog on `main`,
branch into `experiment-cloud-mask-v2`, rerun a stricter cloud classifier, diff against
`main`, merge, then roll back, all through the lakeFS Python SDK. Pairs with the
[`lakefs-on-b2-quickstart`](https://github.com/backblaze-b2-samples/lakefs-on-b2-quickstart)
Docker Compose stack for the lakeFS server. Companion to
[treeverse/lakeFS#10426](https://github.com/treeverse/lakeFS/pull/10426), which added the
`lakefs/<version>` `User-Agent` on every outbound B2 request.

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/backblaze-b2-samples/notebooks/blob/main/lakefs-b2-dataset-versioning/lakefs_b2_dataset_versioning.ipynb) [![Open In Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/backblaze-b2-samples/notebooks/HEAD?urlpath=lab/tree/lakefs-b2-dataset-versioning/lakefs_b2_dataset_versioning.ipynb) [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/backblaze-b2-samples/notebooks?quickstart=1)

## How to run an example

Each example directory has its own `README.md` with detailed setup instructions, but in
short:

* **In a browser**, click one of the launch badges (Colab, Binder, Codespaces) on the
  example you want.
* **Locally**, clone this repo, `cd` into the example directory, and follow its
  `README.md` (typically `pip install -r requirements.txt && jupyter lab <notebook>.ipynb`).

## Backblaze B2 prerequisites

Most examples need a Backblaze B2 application key. Generate one at
<https://www.backblaze.com/docs/cloud-storage-application-keys>, then export the values
as the standard AWS-named environment variables (B2's S3-compatible API reads these
under the AWS SDK):

```bash
export AWS_ENDPOINT_URL_S3="https://s3.<region>.backblazeb2.com"  # region from B2 console
export AWS_ACCESS_KEY_ID="<your B2 application key ID>"
export AWS_SECRET_ACCESS_KEY="<your B2 application key>"
```

For Colab / Codespaces / Kaggle / Binder, see the per-example `README.md` for the
secret-store path that fits each runtime.

## Contributing

New examples are welcome. Each example lives in its own top-level directory and is
expected to include:

* A descriptive `README.md` (purpose, how to run, secret setup if needed)
* The notebook(s) themselves, with launch badges that point at the path on `main`
* A `requirements.txt` (or equivalent) so the example is reproducible
* A `.github/workflows/test-<name>.yml` workflow that executes the notebook
  end-to-end against the shared `backblaze-samples-ci` bucket

See [`CLAUDE.md`](./CLAUDE.md) for the full conventions: writing style (no em
dashes), repo layout, two-bucket pattern, custom `user_agent_extra` on every
B2 boto3 client, headless-execution env vars, pre-commit hooks, and the
per-notebook CI workflow shape.

Before opening a PR, install and run pre-commit locally:

```bash
pip install pre-commit
pre-commit install
pre-commit run --all-files
```

CI runs the same hooks via `.github/workflows/lint.yml` on every push.

## Related

* [Backblaze B2 Cloud Storage](https://www.backblaze.com/cloud-storage)
* [Backblaze developer docs](https://www.backblaze.com/docs/cloud-storage)
* More B2 sample apps across languages and frameworks: <https://github.com/backblaze-b2-samples>
