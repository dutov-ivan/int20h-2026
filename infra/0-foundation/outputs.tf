output "resource_group_name" {
  value = azurerm_resource_group.rg.name
}

output "service_plan_id" {
  value = azurerm_service_plan.plan.id
}

output "service_plan_name" {
  value = azurerm_service_plan.plan.name
}

output "acr_login_server" {
  value = azurerm_container_registry.acr.login_server
}

output "acr_id" {
  value = azurerm_container_registry.acr.id
}

output "acr_name" {
  value = azurerm_container_registry.acr.name
}
