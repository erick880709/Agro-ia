variable "name" {
  description = "Nombre base de los recursos."
  type        = string
}

variable "table_name" {
  description = "Nombre de la tabla DynamoDB a la que escribe el consumidor."
  type        = string
}

variable "table_arn" {
  description = "ARN de la tabla DynamoDB."
  type        = string
}

variable "visibility_timeout" {
  description = "Visibility timeout de la cola en segundos."
  type        = number
  default     = 30
}
