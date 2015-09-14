provider "aws" {
    access_key = "${var.aws_access_key}"
    secret_key = "${var.aws_secret_key}"
    region = "${var.aws_region}"
}
resource "aws_instance" "master" {
    ami = "${lookup(var.aws_ubuntu_amis, var.aws_region)}"
    instance_type = "${var.aws_instance_type}"
    availability_zone = "${var.aws_availability_zone}"
}
resource "aws_instance" "nodes" {
    ami = "${lookup(var.aws_ubuntu_amis, var.aws_region)}"
    instance_type = "${var.aws_instance_type}"
    availability_zone = "${var.aws_availability_zone}"
    count = 3
}
