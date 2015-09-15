provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "${var.aws_region}"
}
resource "aws_security_group" "cluster_security_group" {
  name = "flocker_rules"
  description = "Allow SSH, HTTP, Flocker APIs"
  # ssh
  ingress {
      from_port = 22
      to_port = 22
      protocol = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
  }
  # http for demo
  ingress {
      from_port = 80
      to_port = 80
      protocol = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
  }
  # external flocker api
  ingress {
      from_port = 4523
      to_port = 4523
      protocol = "tcp"
      cidr_blocks = ["0.0.0.0/0"]
  }
  # internal flocker-control port
  ingress {
      from_port = 4524
      to_port = 4524
      protocol = "tcp"
      self = true
  }
  # allow outbound traffic
  egress {
      from_port = 0
      to_port = 0
      protocol = "-1"
      cidr_blocks = ["0.0.0.0/0"]
  }
}
resource "aws_instance" "master" {
    ami = "${lookup(var.aws_ubuntu_amis, var.aws_region)}"
    instance_type = "${var.aws_instance_type}"
    availability_zone = "${var.aws_availability_zone}"
    security_groups = ["${aws_security_group.cluster_security_group.name}"]
    key_name = "${var.aws_key_name}"
}
resource "aws_instance" "nodes" {
    ami = "${lookup(var.aws_ubuntu_amis, var.aws_region)}"
    instance_type = "${var.aws_instance_type}"
    availability_zone = "${var.aws_availability_zone}"
    count = 3
    security_groups = ["${aws_security_group.cluster_security_group.name}"]
    key_name = "${var.aws_key_name}"
}
