variable "name" {
  description = "Base name used for created resources."
  type        = string
}

variable "force_destroy" {
  description = "Allow the bucket to be destroyed even if it contains objects."
  type        = bool
  default     = false
}

variable "enable_alert_topic" {
  description = "Whether to create the SNS alert topic."
  type        = bool
  default     = true
}

variable "alert_email" {
  description = "Optional email subscribed to the alert topic."
  type        = string
  default     = ""
}
