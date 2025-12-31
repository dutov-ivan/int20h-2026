variable "prefix" {
  type        = string
  description = "Name prefix for resources"
  default     = "int20h"
}

variable "resource_group_name" {
  type        = string
  description = "Resource group name"
}

variable "location" {
  type        = string
  description = "Azure location"
  default     = "westus2"
}

variable "service_plan_sku_tier" {
  type        = string
  description = "App Service Plan tier (e.g., Basic)"
  default     = "Basic"
}

variable "service_plan_sku_size" {
  type        = string
  description = "App Service Plan size (e.g., B1)"
  default     = "B1"
}

variable "service_plan_sku_capacity" {
  type        = number
  description = "App Service Plan capacity"
  default     = 1
}

variable "acr_name" {
  type        = string
  description = "Azure Container Registry name"
}
