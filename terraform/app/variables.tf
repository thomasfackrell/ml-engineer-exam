variable "container_image_tag" {
  type        = string
  description = "The tag of the Docker image to deploy (usually the Git SHA)"
  default     = "latest" # Fallback for local testing
}

variable "enable_auth" {
  type        = bool
  description = "Toggle to enable or disable JWT authentication for the API"
  default     = false # Default to off for easier reviewer testing
}

variable "oidc_issuer" {
  type        = string
  description = "The OIDC issuer URL (e.g., https://dev-xxxx.auth0.com/)"
  default     = ""
}

variable "oidc_audience" {
  type        = list(string)
  description = "The expected audience for the JWT"
  default     = []
}