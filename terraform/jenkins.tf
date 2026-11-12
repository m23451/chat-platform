resource "aws_iam_user" "jenkins" {
  name = "${var.name}-jenkins"
}

data "aws_iam_policy_document" "jenkins_ecr_push" {
  statement {
    actions   = ["ecr:GetAuthorizationToken"]
    resources = ["*"]
  }

  # push read roles for ecr repo
  statement {
    actions = [
      "ecr:BatchCheckLayerAvailability",
      "ecr:InitiateLayerUpload",
      "ecr:UploadLayerPart",
      "ecr:CompleteLayerUpload",
      "ecr:PutImage",
      "ecr:BatchGetImage",
    ]
    resources = [for r in aws_ecr_repository.repos : r.arn]
  }
}

resource "aws_iam_user_policy" "jenkins_ecr_push" {
  name   = "ecr-push-only"
  user   = aws_iam_user.jenkins.name
  policy = data.aws_iam_policy_document.jenkins_ecr_push.json
}