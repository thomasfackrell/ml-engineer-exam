FROM public.ecr.aws/lambda/python:3.12

# 1. Install uv for fast, reliable dependency management
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the Lambda task root
WORKDIR ${LAMBDA_TASK_ROOT}

# 2. Compatibility Layer for Python 3.12 (MLflow/Protobuf legacy support)
ENV SETUPTOOLS_USE_DISTUTILS=local
RUN pip install --no-cache-dir "setuptools>=69.0.0" wheel

# 3. Copy only the dependency definitions first (optimization for layer caching)
COPY pyproject.toml uv.lock ./

# 4. SURGICAL COPY: Only the core package
# We copy the specific package folder instead of the whole 'src' directory
COPY src/ml_engineer_exam ./src/ml_engineer_exam

# 5. Install dependencies and the project as a system package
# This makes 'import ml_engineer_exam' work anywhere in the container
RUN uv pip install . --system

# 6. COPY: Model artifacts
# We preserve the 'data/models' pathing so MLDeployConfig can find them
COPY data/models ./data/models

# 7. Environment Variables to resolve your Pathlib TypeError
# This tells your config.py exactly where the root is
ENV ROOT_PATH=${LAMBDA_TASK_ROOT}
ENV APP_NAME=ml_engineer_exam

# 8. SECURITY: Use a non-root user for execution
# Lambda RIE (local) and production Lambda support non-root users
RUN useradd -u 1001 appuser
USER appuser

CMD [ "ml_engineer_exam.handler.lambda_handler" ]