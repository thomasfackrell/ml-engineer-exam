FROM public.ecr.aws/lambda/python:3.12

# 1. Install uv for fast, reliable dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# Update OS packages to patch glibc vulnerabilities (CVE-2026-4046)
RUN dnf update -y --releasever=latest glibc glibc-common glibc-langpack-en glibc-minimal-langpack && \
    dnf clean all

# 2. Compatibility Layer for Python 3.12 (MLflow/Protobuf legacy support)
ENV SETUPTOOLS_USE_DISTUTILS=local
RUN pip install --no-cache-dir "setuptools>=69.0.0" wheel

# 3. Copy only the dependency definitions first (optimization for layer caching)
COPY requirements.txt pyproject.toml uv.lock ./

# 4. SURGICAL COPY: Only the core package
# We copy the specific package folder instead of the whole 'src' directory
COPY src/ml_engineer_exam ./src/ml_engineer_exam

# 5. Use uv sync to honor the lockfile versions explicitly
RUN uv pip sync requirements.txt --system

# 6. COPY: Model artifacts
# We preserve the 'data/models' pathing so MLDeployConfig can find them
COPY data/models ./data/models

# 7. Environment Variables to resolve your Pathlib TypeError
# This tells your config.py exactly where the root is
ENV ROOT_PATH=${LAMBDA_TASK_ROOT}
ENV APP_NAME=ml_engineer_exam

# 8. SECURITY: Use a non-root user for execution
# We create 'appuser' natively for simplicity and security
RUN echo "appuser:x:1001:1001::/home/appuser:/bin/bash" >> /etc/passwd && \
    echo "appuser:x:1001:" >> /etc/group

    # Ensure appuser owns the runtime paths and python global libraries
RUN chown -R appuser:appuser ${LAMBDA_TASK_ROOT} /var/lang/

USER appuser

CMD [ "ml_engineer_exam.handler.lambda_handler" ]