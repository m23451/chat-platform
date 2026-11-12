module "eks" {
  source  = "terraform-aws-modules/eks/aws"
  version = "~> 21.0"

  name = var.name

  kubernetes_version = "1.37"

  endpoint_public_access = true

  enable_cluster_creator_admin_permissions = true

  vpc_id     = module.vpc.vpc_id

  subnet_ids = module.vpc.public_subnets

  addons = {
    vpc-cni = {
      before_compute = true
    }
    eks-pod-identity-agent = {
      before_compute = true
    }
    kube-proxy         = {}
    coredns            = {}
    aws-ebs-csi-driver = {}
  }


  eks_managed_node_groups = {
    default = {
      instance_types = ["t3.large"]   # 2 CPU, 8 GB RAM each
      capacity_type  = "ON_DEMAND"    # "SPOT" is ~60% cheaper but can be interrupted
      min_size       = 1
      max_size       = 3
      desired_size   = 2
    }
  }
}


module "ebs_csi_pod_identity" {
  source  = "terraform-aws-modules/eks-pod-identity/aws"
  version = "~> 2.0"

  name                      = "${var.name}-ebs-csi"
  attach_aws_ebs_csi_policy = true

  associations = {
    ebs = {
      cluster_name    = module.eks.cluster_name
      namespace       = "kube-system"
      service_account = "ebs-csi-controller-sa"
    }
  }
}