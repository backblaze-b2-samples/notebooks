# PyTorch image classification on Backblaze B2

End-to-end example showing how to use [Backblaze B2](https://www.backblaze.com/cloud-storage)
as both the **input data store** and the **checkpoint destination** for
training a [PyTorch](https://pytorch.org/) image classifier on
[CIFAR-10](https://www.cs.toronto.edu/~kriz/cifar.html).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/drive/1cOjN8ySp6wj_i6ZlH8qulRTCV8japlHN#scrollTo=74dOjOK6CEAD) [![Open In Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/backblaze-b2-samples/notebooks/HEAD?urlpath=lab/tree/image-classification-pytorch/cifar10_b2_pytorch_training.ipynb) [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/backblaze-b2-samples/notebooks?quickstart=1)

## What's in this directory

| File | Purpose |
|---|---|
| `cifar10_b2_pytorch_training.ipynb` | Main notebook. Streams CIFAR-10 images from a public B2 bucket via a custom PyTorch `Dataset`, fine-tunes a pretrained ResNet-18 on 10 image classes, saves the resulting checkpoint to a private B2 bucket of yours, and runs inference on user-uploaded images. |
| `requirements.txt` | Pip dependencies. Used by Binder (and any user who wants to recreate the env locally). |

## Why this works

Backblaze B2 exposes an S3-compatible API. The notebook talks to B2 with
plain `boto3.client("s3", endpoint_url=...)`, no Backblaze-specific
plumbing required. The custom `Dataset` uses the same client to fetch
training and test images on demand, so memory stays flat regardless of
dataset size.

The boto3 client is configured with:

| Field | Value |
|---|---|
| `endpoint_url` | `https://s3.<region>.backblazeb2.com` (region from your B2 bucket settings) |
| `aws_access_key_id` | your B2 application key ID |
| `aws_secret_access_key` | your B2 application key |
| `config.signature_version` | `s3v4` |
| `config.user_agent_extra` | `b2-notebook-pytorch` (so B2 server-side logs can identify traffic from this notebook) |

Generate a B2 application key at
<https://www.backblaze.com/docs/cloud-storage-application-keys>.

## Two distinct buckets

Backblaze B2 bucket privacy is set at the bucket level: a "Public" bucket
is anonymously readable but **never** publicly writable. The notebook
accordingly uses two buckets:

* **Read**, the public `odh-datasets` bucket holding the CIFAR-10
  training and test images, organized in `train/<class>/*.png` and
  `test/<class>/*.png` folders. The notebook ships with a pre-shared
  read-only application key so the demo runs without anyone having to
  generate one.
* **Write**, a *separate* private B2 bucket of yours, with an application
  key that has write access to it. This is where the trained ResNet-18
  checkpoint and the inference results land.

## Running the notebook (and where to put credentials)

For the write path the notebook needs your private-bucket name, region,
and B2 application key. It currently asks for them via interactive
`input()` / `getpass()` prompts at the top of section *Your B2 Bucket for
Outputs*; you can also export them as env vars beforehand and edit the
cell to read those instead.

| Environment | Secret store | Notes |
|---|---|---|
| **GitHub Codespaces** &#11088; | User Settings &rarr; Codespaces &rarr; *Codespaces secrets* | Recommended. Add `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`, scope them to `backblaze-b2-samples/notebooks`. Click the Codespaces badge above to launch. |
| **Google Colab** | Left sidebar &rarr; &#128273; *Secrets* | Add the two secrets and grant this notebook access. |
| **Binder** | None (ephemeral by design) | The notebook's interactive prompts ask for credentials at runtime. They stay in the running kernel only. |
| **Local Jupyter / shell** | Shell env | `export AWS_ACCESS_KEY_ID=...; export AWS_SECRET_ACCESS_KEY=...` before launching, or run `jupyter lab` and type them at the prompt. |

For a fully local install:

```bash
pip install -r requirements.txt
jupyter lab cifar10_b2_pytorch_training.ipynb
```

The notebook runs on CPU. ResNet-18 fine-tuning on CIFAR-10 takes 5 to 10
minutes per epoch on a recent laptop; the default training schedule is
short on purpose so the demo finishes in a reasonable wall-clock time.
Bump epochs or switch to GPU for higher final accuracy.

## What you'll see when it runs

1. **Section 1 (Setup)**: installs `boto3`, `torch`, `torchvision`, and the
   imaging deps.
2. **Section 2 (Configuration)**: builds the read-only B2 client for the
   public CIFAR-10 bucket, then prompts for *your* write-bucket
   credentials.
3. **Section 3 (List & Load)**: enumerates the train/test prefix on the
   public bucket and wraps it in a streaming PyTorch `Dataset` +
   `DataLoader`.
4. **Section 4 (Train)**: loads a pretrained ResNet-18, replaces the final
   layer for 10-class output, trains, evaluates, prints loss/accuracy.
5. **Section 5 (Save)**: uploads the trained checkpoint and a results JSON
   to your private bucket.
6. **Section 6 (Inference)**: lets you upload an arbitrary image and runs
   the trained model on it, displaying the top-3 predicted classes.

## Related

* [Backblaze B2 Cloud Storage Application Keys](https://www.backblaze.com/docs/cloud-storage-application-keys),
  how to generate the keys plugged into `AWS_ACCESS_KEY_ID` /
  `AWS_SECRET_ACCESS_KEY` (or asked for at the notebook prompts).
* [PyTorch transfer-learning tutorial](https://docs.pytorch.org/tutorials/beginner/transfer_learning_tutorial.html),
  the upstream reference for the fine-tuning pattern used here.
* Sibling examples in this repo: <https://github.com/backblaze-b2-samples/notebooks>
