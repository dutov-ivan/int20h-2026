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
