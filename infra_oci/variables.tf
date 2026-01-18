variable "tenancy_ocid" {}
variable "user_ocid" {}
variable "fingerprint" {}
variable "private_key_path" {}
variable "compartment_ocid" {}
variable "region" {default = "us-ashburn-1"}
variable "ssh_public_key_path" {
  default = "/home/fabio_dev/chaves_oracle/ssh_key_hackathon.pub"
}