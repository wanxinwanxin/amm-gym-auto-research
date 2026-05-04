# vendored-wheels/

Pre-built Python wheels for installing `jax` (and dependencies) inside the
ARM64 Linux sandbox without touching the network or building from source.

## Why

The autoresearch sandbox has 3.9 GB total RAM and no swap. `pip install jax`
triggers a wheel build for at least one transitive dep and OOMs (exit 143)
during compile. See `bin/checks/08_jax_optional.sh` and the "Blockers for
user" section of `research/STATE.md` for context.

These wheels match the sandbox spec:

- Python 3.10 (cp310 / abi cp310)
- Linux glibc 2.35
- aarch64 (manylinux2014 / manylinux_2_17 aarch64)

`bin/setup_jax_from_vendored.sh` installs from this directory with
`pip install --no-index --find-links=vendored-wheels jax jaxlib`, so pip
cannot reach PyPI and cannot trigger a build.

## What is vendored

| package      | version | size  | notes                                  |
|--------------|---------|-------|----------------------------------------|
| jax          | 0.6.2   | 2.6M  | pure-Python                            |
| jaxlib       | 0.6.2   | 76M   | CPU-only XLA runtime, manylinux2014    |
| ml_dtypes    | 0.5.1   | 4.4M  | jax dep                                |
| opt_einsum   | 3.4.0   | 70K   | jax dep, pure-Python                   |
| numpy        | 2.2.6   | 14M   | jax requires >=1.26                    |
| scipy        | 1.15.3  | 34M   | jax requires >=1.12                    |

Vendored on **2026-05-05**. Total ~130 MB.

`numpy` and `scipy` are included because jax 0.6.2 requires versions newer
than what older sandboxes may carry; pip will upgrade only if the resident
versions don't already satisfy jax's pins. The repo itself requires
`numpy>=1.24`, which numpy 2.2.6 satisfies.

## How to refresh

From a host that has network access (e.g. your laptop):

```bash
rm vendored-wheels/*.whl
pip3 download \
  --only-binary=:all: \
  --platform manylinux2014_aarch64 \
  --python-version 3.10 \
  --implementation cp \
  --abi cp310 \
  -d vendored-wheels \
  jax jaxlib
```

Then update the version table above and commit.

If `pip download` fails to resolve a clean wheel set (occasionally happens
when a new jax release has a transitive dep with no aarch64 wheel yet),
pin to the previous minor — e.g. `jax==0.6.1 jaxlib==0.6.1` — and retry.
