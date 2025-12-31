output "web_app_default_hostname" {
  value = azurerm_linux_web_app.bot.default_hostname
}

output "web_app_identity_principal_id" {
  value = azurerm_linux_web_app.bot.identity[0].principal_id
}
