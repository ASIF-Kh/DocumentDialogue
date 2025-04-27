# FROM python:3.11-slim

# # Set working directory
# WORKDIR /app

# # Install uv globally
# RUN pip install uv


# # Copy the entire project into the container
# COPY . /app

# # Install dependencies from pyproject.toml using uv
# RUN uv sync --python /usr/local/bin/python

# Install uv
FROM python:3.12-slim
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Change the working directory to the `app` directory
WORKDIR /app

# Install dependencies
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    uv sync --locked --no-install-project

# Copy the project into the image
ADD . /app

# Sync the project
RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

# Expose the port your app will run on
EXPOSE 8000

# Presuming there is a `my_app` command provided by the project
CMD ["uv", "run", "main.py"]
