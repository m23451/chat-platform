resource "aws_ecr_repository" "repos" {
  for_each = toset(["chat-api", "chat-frontend"])

  name = "${var.name}/${each.key}"
  image_tag_mutability = "MUTABLE"
  force_delete = true

  image_scanning_configuration {
    scan_on_push = true
  }
}

output "ecr_urls" {
value = { for k, r in aws_ecr_repository.repos : k => r.repository_url }
}