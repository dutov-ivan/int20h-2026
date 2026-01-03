terraform {
  required_version = ">= 1.1.0"

  backend "azurerm" {
    resource_group_name  = "rg-terraform-state"
    storage_account_name = "int20htfstate"
    container_name       = "tfstate"
  }
  required_providers {
    azurerm = {
      source  = "hashicorp/azurerm"
      version = ">= 3.0.0"
    }
  }
}

provider "azurerm" {
  features {}
}

resource "azurerm_resource_group" "rg" {
  name     = var.resource_group_name
  location = var.location
}

resource "azurerm_service_plan" "plan" {
  name                = var.service_plan_name
  location            = azurerm_resource_group.rg.location
  resource_group_name = var.resource_group_name
  os_type                = "Linux"

  sku_name = var.service_plan_sku_size
}

resource "azurerm_container_registry" "acr" {
  name                = var.acr_name
  resource_group_name = var.resource_group_name
  location            = azurerm_resource_group.rg.location
  sku                 = "Basic"
  admin_enabled       = false
}