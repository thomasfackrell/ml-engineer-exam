# ==========================================
# STAGE 1: Base Setup (Shared Production Layer)
# ==========================================
FROM public.ecr.aws/lambda/python:3.12 AS base
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/
WORKDIR ${LAMBDA_TASK_ROOT}

RUN dnf update -y --releasever=latest glibc glibc-common glibc-langpack-en glibc-minimal-langpack && \
    dnf clean all

ENV SETUPTOOLS_USE_DISTUTILS=local
RUN pip install --no-cache-dir "setuptools>=69.0.0" wheel

# Copy production-only dependencies
COPY requirements.txt pyproject.toml uv.lock ./
COPY src/ml_engineer_exam ./src/ml_engineer_exam
RUN uv pip install --system -r requirements.txt

# ==========================================
# STAGE 2: Test Environment (With awslambdaric)
# ==========================================
FROM base AS test-env
RUN uv pip install awslambdaric --system
COPY data/models ./data/models

RUN echo "appuser:x:1001:1001::/home/appuser:/bin/bash" >> /etc/passwd && \
    echo "appuser:x:1001:" >> /etc/group && \
    chown -R appuser:appuser ${LAMBDA_TASK_ROOT}
USER appuser
CMD [ "ml_engineer_exam.handler.lambda_handler" ]

# ==========================================
# STAGE 3: Pristine Production Runtime (No Dev Bloat!)
# ==========================================
FROM base AS production
COPY data/models ./data/models

RUN echo "appuser:x:1001:1001::/home/appuser:/bin/bash" >> /etc/passwd && \
    echo "appuser:x:1001:" >> /etc/group && \
    chown -R appuser:appuser ${LAMBDA_TASK_ROOT}
USER appuser
CMD [ "ml_engineer_exam.handler.lambda_handler" ]