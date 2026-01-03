variable "resource_group_name" {
  type        = string
  description = "Resource group created in foundation layer"
}

variable "service_plan_name" {
  type        = string
  description = "App Service Plan name created in foundation layer"
}

variable "acr_name" {
  type        = string
  description = "ACR name created in foundation layer"
}

variable "app_name" {
  type        = string
  description = "Name of the Web App"
}

variable "docker_image" {
  type        = string
  description = "Container image to deploy (e.g., myacr.azurecr.io/bot:v1)"
}

variable "app_settings" {
  type        = map(string)
  description = "Application settings to pass to the Web App"
  default     = {}
}

variable "BOT_TOKEN" {
  type        = string
  description = "Bot token for the customer bot"
  sensitive   = true
}

variable "FORUM_GROUP_ID" {
  type        = string
  description = "Forum group ID for the customer bot"
  sensitive = true
}

variable "DATABASE_URL" {
  type        = string
  description = "Database connection string"
  sensitive   = true
}

variable "WEBHOOK_SECRET_TOKEN" {
  type        = string
  description = "Secret token to verify incoming webhooks"
  sensitive   = true
}

variable "ENVIRONMENT" {
  type        = string
  description = "Environment the app is deployed in (staging/production)"
}

variable "WEBSITES_PORT" {
  type        = string
  description = "Port on which the app listens"
  default     = "8000"
}
