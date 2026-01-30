# [Choice] Python version (use -bookworm or -bullseye variants on local arm64/Apple Silicon): 3, 3.13, 3.12, 3.11, 3.10, 3.9, 3-bookworm, 3.13-bookworm, 3.12-bookworm, 3.11-bookworm, 3.10-bookworm, 3.9-bookworm, 3-bullseye, 3.13-bullseye, 3.12-bullseye, 3.11-bullseye, 3.10-bullseye, 3.9-bullseye, 3-buster, 3.12-buster, 3.11-buster, 3.10-buster, 3.9-buster
ARG VARIANT=3-trixie
FROM python:${VARIANT}

RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    # Remove imagemagick due to https://security-tracker.debian.org/tracker/CVE-2019-10131
    && apt-get purge -y imagemagick imagemagick-6-common 

# Temporary: Upgrade python packages due to https://cve.mitre.org/cgi-bin/cvename.cgi?name=CVE-2022-40897 and https://github.com/advisories/GHSA-2mqj-m65w-jghx
# They are installed by the base image (python) which does not have the patch.
RUN python3 -m pip install --upgrade \
    setuptools==78.1.1 \
    gitpython==3.1.41


# [Optional] If your pip requirements rarely change, uncomment this section to add them to the image.
# COPY requirements.txt /tmp/pip-tmp/
# RUN pip3 --disable-pip-version-check --no-cache-dir install -r /tmp/pip-tmp/requirements.txt \
#    && rm -rf /tmp/pip-tmp

# [Optional] Uncomment this section to install additional OS packages.
RUN apt-get update && export DEBIAN_FRONTEND=noninteractive \
    && apt-get -y install --no-install-recommends ffmpeg

COPY --from=docker.io/astral/uv:latest /uv /usr/local/bin/uv

# Set the working directory inside the container
WORKDIR /workspaces
COPY main.py /workspaces
COPY pyproject.toml /workspaces
COPY README.md /workspaces

RUN uv sync

ENV PORT=8000
ENV DOWNLOAD_PATH=/workspaces/downloads
ENV FFMPEG_LOCATION=/usr/bin/ffmpeg

# Expose the port on which the FastAPI app will run
EXPOSE $PORT

# Set the command to run the FastAPI app when the container starts
ENTRYPOINT ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "$PORT"]
