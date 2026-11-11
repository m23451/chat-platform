variable "region" {
    description = "AWS region to build in"
    type        = string
    default     = "eu-north-1"
}

variable "name" {
    description = "prefix"
    type = string
    default = "chat-site"
    }