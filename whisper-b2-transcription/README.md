# Whisper audio transcription on Backblaze B2

End-to-end example showing how to use [Backblaze B2](https://www.backblaze.com/cloud-storage)
as both the **input audio store** and the **transcript output destination** for
speech-to-text transcription with [OpenAI Whisper](https://github.com/openai/whisper).

[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/backblaze-b2-samples/notebooks/blob/main/whisper-b2-transcription/whisper_b2_transcription.ipynb) [![Open In Binder](https://mybinder.org/badge_logo.svg)](https://mybinder.org/v2/gh/backblaze-b2-samples/notebooks/HEAD?urlpath=lab/tree/whisper-b2-transcription/whisper_b2_transcription.ipynb) [![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/backblaze-b2-samples/notebooks?quickstart=1)

## What's in this directory

| File | Purpose |
|---|---|
| `whisper_b2_transcription.ipynb` | Main notebook. Streams `jfk.flac` from a public B2 bucket via an anonymous boto3 client, runs Whisper for ASR, optionally writes the transcript JSON back to a private bucket. |
| `prepare_dataset.py` | One-off script to fetch `jfk.flac` from the openai/whisper repo (public domain) and upload it to a B2 bucket of your choice. |
| `requirements.txt` | Pip dependencies. Used by Binder and any user who wants to recreate the env locally. |

## Why this works

Backblaze B2 exposes an S3-compatible API. The notebook talks to B2 with plain
`boto3.client("s3", endpoint_url=...)`, twice:

1. An **anonymous** client (`signature_version=UNSIGNED`) for the public read of
   `b2datasets/whisper-demo/jfk.flac`. Anonymous GETs are allowed on B2 Public
   buckets; anonymous LISTs are not, but we don't need to list, only GET one
   known key.
2. An **authenticated** client built from your B2 application key for the write
   to a private bucket of your own.

Both clients pin `region_name` explicitly (`us-west-001` for the read,
your bucket's region for the write) and set
`user_agent_extra="b2-notebook-whisper"` so requests are attributable on B2's
server-side logs.

Generate a B2 application key at
<https://www.backblaze.com/docs/cloud-storage-application-keys>.

## Two distinct buckets

Backblaze B2 bucket privacy is set at the bucket level: a "Public" bucket is
anonymously readable but **never** publicly writable. The notebook accordingly
uses two buckets:

* **Read**, the public `b2datasets` bucket holding the JFK demo audio. No
  credentials needed.
* **Write**, a *separate* private B2 bucket of yours, with an application key
  that has write access to it. This is where transcript JSON lands. May be in
  any B2 region (`PRIVATE_B2_REGION` env var or interactive prompt).

## Running the notebook (and where to put credentials)

The write path needs `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY` plus
`PRIVATE_B2_BUCKET` + `PRIVATE_B2_REGION`. The read path is anonymous.

| Environment | Secret store | Notes |
|---|---|---|
| **GitHub Codespaces** &#11088; | User Settings &rarr; Codespaces &rarr; *Codespaces secrets* | Add the four values as secrets scoped to `backblaze-b2-samples/notebooks`. Injected as env vars natively. |
| **Google Colab** | Left sidebar &rarr; &#128273; *Secrets* | Add `AWS_ACCESS_KEY_ID` + `AWS_SECRET_ACCESS_KEY`; the notebook reads them via `google.colab.userdata.get(...)`. Bucket name + region prompted interactively. |
| **Binder** | None (ephemeral by design) | Falls back to `getpass.getpass()` and `input()` for all four. |
| **Local Jupyter / shell** | Shell env | `export AWS_ACCESS_KEY_ID=...` etc. before launching, or type at the prompts. |

For a fully local install:

```bash
pip install -r requirements.txt
jupyter lab whisper_b2_transcription.ipynb
```

The default `tiny` Whisper model runs in seconds on CPU. Switch to higher
quality via `WHISPER_MODEL_SIZE=base` (or `small` / `medium` / `large`) before
launching the notebook.

## What you'll see when it runs

1. **Setup**: installs `openai-whisper` and `boto3`.
2. **Configuration**: prints the read endpoint + prompts for your write bucket
   (skippable).
3. **Stream the audio from B2**: downloads `jfk.flac` (~390 KB) to a temp file.
4. **Transcribe with Whisper**: loads the model, prints detected language +
   transcript text.
5. **(Optional) Persist**: writes the full Whisper JSON result back to your
   private B2 bucket.

## Pre-flight: stage the audio file

If the demo audio isn't already in `b2datasets/whisper-demo/`, run:

```bash
export AWS_ACCESS_KEY_ID=<your B2 application key id>
export AWS_SECRET_ACCESS_KEY=<your B2 application key>
python prepare_dataset.py --bucket b2datasets --prefix whisper-demo
```

This downloads `jfk.flac` from the openai/whisper repo (~390 KB) and uploads it
to `s3://b2datasets/whisper-demo/jfk.flac`.

## Related

* [OpenAI Whisper](https://github.com/openai/whisper) project page.
* [Backblaze B2 Cloud Storage Application Keys](https://www.backblaze.com/docs/cloud-storage-application-keys).
* Sibling examples in this repo: <https://github.com/backblaze-b2-samples/notebooks>
