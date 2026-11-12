data "aws_availability_zones" "available" {
  state = "available"
}


module "vpc" {
  source  = "terraform-aws-modules/vpc/aws"
  version = "~> 6.0"

  name = var.name
  cidr = "10.0.0.0/16"

  # Two availability zones due to eks requirements of atleast 2
  azs            = slice(data.aws_availability_zones.available.names, 0, 2)
  public_subnets = ["10.0.1.0/24", "10.0.2.0/24"]


  # Production would use private subnets + a NAT gateway.
  map_public_ip_on_launch = true
  enable_nat_gateway      = false
  enable_dns_hostnames    = true

  # Kubernetes put public load balancers
  public_subnet_tags = {
    "kubernetes.io/role/elb" = 1
  }
}