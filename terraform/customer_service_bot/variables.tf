variable "location" {
  default = "East US"
}

variable "app_service_sku" {
  description = "The size of the VM (F1, B1, S1)"
}

variable "database_url" {
  description = "The database connection URL"
  type = string
  sensitive   = true
}

variable "random_suffix" {
  description = "Random string to make DNS unique"
  default     = "xyz" 
}

variable "customer_service_bot_api_key" {
  description = "API key for the customer service bot"
  sensitive   = true
}

variable "customer_service_forum_id" {
  description = "Forum ID for the customer service bot"
  type = number
  sensitive   = true
}

variable "customer_service_webhook_secret_token" {
  description = "Webhook secret token for the customer service bot"
  type = string
  sensitive   = true
}

variable "environment" {
  description = "The deployment environment (e.g., development, staging, production)"
  default     = "production"
}