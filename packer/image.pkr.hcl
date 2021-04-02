data "amazon-ami" "canonical-ubuntu" {
  filters = {
    name                = "ubuntu/images/hvm-ssd/ubuntu-bionic-18.04-amd64-server-*"
    root-device-type    = "ebs"
    virtualization-type = "hvm"
  }
  most_recent = true
  owners      = ["099720109477"]
  region      = "ap-southeast-1"
}

variable "service" {
  type = string
}

source "amazon-ebs" "image" {
  # AMI Configuration
  ami_name                = "peter-${var.service}-{{ timestamp }}"
  ami_description         = "AMI with necessary installation for ${var.service}"
  ami_virtualization_type = "hvm"
  ami_users = [
    "406178986850",
  ]
  ami_regions = [
    "ap-southeast-1",
  ]
  tag {
    key   = "Name"
    value = "peter-${var.service}"
  }

  # Access Configuration
  region = "ap-southeast-1"

  # Run Configuration
  instance_type               = "t2.micro"
  source_ami                  = data.amazon-ami.canonical-ubuntu.id
  associate_public_ip_address = true
  ebs_optimized               = false
  subnet_id                   = "subnet-0c4de58d62790a2a3"
  # subnet_filter {
  #   filters = {
  #     "tag:Name" : "pub-defaut-1c-1",
  #   }
  #   most_free = true
  #   random    = true
  # }
  vpc_filter {
    filters = {
      "tag:Name" : "default",
    }
  }
  ssh_interface = "public_ip"

  # Block Devices Configuration
  launch_block_device_mappings {
    device_name           = "/dev/sda1"
    delete_on_termination = true
    volume_type           = "gp2"
    volume_size           = 16
  }

  # Communicator Configuration
  ssh_username = "ubuntu"
}

build {
  sources = [
    "source.amazon-ebs.image",
  ]

  provisioner "shell" {
    inline = [
      "while [ ! -f /var/lib/cloud/instance/boot-finished ]; do echo 'Waiting for cloud-init...'; sleep 1; done",
    ]
  }

  provisioner "ansible" {
    playbook_file = "./packer/${var.service}/build.yml"
  }

  post-processor "manifest" {
    output = "${var.service}.manifest.json"
  }
}
