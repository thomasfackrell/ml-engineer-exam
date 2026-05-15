# 1. ECR Repository to store the Docker Image
resource "aws_ecr_repository" "app_repo" {
  name                 = "ml-engineer-exam" # Derived from project name
  image_tag_mutability = "MUTABLE"
  force_delete         = true # Facilitates easy cleanup during assessment cycles
}

# 2. IAM Role and Execution Policy for Lambda
resource "aws_iam_role" "lambda_exec" {
  name = "housing_inference_lambda_role"

  assume_role_policy = jsonencode({
    Version = "2012-10-17"
    Statement = [{
      Action = "sts:AssumeRole"
      Effect = "Allow"
      Principal = { Service = "lambda.amazonaws.com" }
    }]
  })
}

# Attach standard logging permissions
resource "aws_iam_role_policy_attachment" "lambda_logs" {
  role       = aws_iam_role.lambda_exec.name
  policy_arn = "arn:aws:iam::aws:policy/service-role/AWSLambdaBasicExecutionRole"
}

# 3. Lambda Function (Container Image based)
resource "aws_lambda_function" "inference_service" {
  function_name = "HousingInferenceService"
  role          = aws_iam_role.lambda_exec.arn
  package_type  = "Image"
  
  # Image URI is parameterized to allow specific Git SHA tagging in CI/CD
  image_uri = "${aws_ecr_repository.app_repo.repository_url}:${var.container_image_tag}"

  timeout     = 30
  memory_size = 1024 # Allocated to handle Random Forest model and MLflow overhead

  environment {
    variables = {
      APP_NAME             = "ml_engineer_exam" # Matches internal config
      ENABLE_MLFLOW        = "false"            # Toggled via environment variable
      MLFLOW_TRACKING_URI  = "http://your-remote-server:5000"
    }
  }
}

# 4. API Gateway v2 (HTTP API)
resource "aws_apigatewayv2_api" "inference_api" {
  name          = "housing-inference-api"
  protocol_type = "HTTP"
}

resource "aws_apigatewayv2_stage" "default" {
  api_id      = aws_apigatewayv2_api.inference_api.id
  name        = "$default"
  auto_deploy = true
}

# 5. Conditional JWT Authorizer (OIDC Compatible)
resource "aws_apigatewayv2_authorizer" "jwt_auth" {
  count            = var.enable_auth ? 1 : 0
  api_id           = aws_apigatewayv2_api.inference_api.id
  name             = "oidc-authorizer"
  authorizer_type  = "JWT"
  identity_sources = ["$request.header.Authorization"]

  jwt_configuration {
    issuer   = var.oidc_issuer
    audience = var.oidc_audience
  }
}

# 6. Integration and Route with Toggleable Security
resource "aws_apigatewayv2_integration" "lambda_integration" {
  api_id           = aws_apigatewayv2_api.inference_api.id
  integration_type = "AWS_PROXY"
  integration_uri  = aws_lambda_function.inference_service.invoke_arn
}

resource "aws_apigatewayv2_route" "predict_route" {
  api_id    = aws_apigatewayv2_api.inference_api.id
  route_key = "POST /predict"
  target    = "integrations/${aws_apigatewayv2_integration.lambda_integration.id}"

  # Conditional auth configuration based on var.enable_auth
  authorization_type = var.enable_auth ? "JWT" : "NONE"
  authorizer_id      = var.enable_auth ? aws_apigatewayv2_authorizer.jwt_auth[0].id : null
}

# 7. Grant API Gateway permission to invoke Lambda
resource "aws_lambda_permission" "apigw_lambda" {
  statement_id  = "AllowExecutionFromAPIGateway"
  action        = "lambda:InvokeFunction"
  function_name = aws_lambda_function.inference_service.function_name
  principal     = "apigateway.amazonaws.com"
  source_arn    = "${aws_apigatewayv2_api.inference_api.execution_arn}/*/*"
}