variable "name" {
  description = "Nombre de la tabla."
  type        = string
}

variable "hash_key" {
  description = "Atributo de partición."
  type        = string
}

variable "hash_key_type" {
  description = "Tipo del atributo de partición (S, N o B)."
  type        = string
  default     = "S"
}

variable "billing_mode" {
  description = "PAY_PER_REQUEST o PROVISIONED."
  type        = string
  default     = "PAY_PER_REQUEST"
}
