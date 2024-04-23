import pulumi
import pulumi_aws as aws

# Create a VPC in the eu-central-1 region
vpc = aws.ec2.Vpc("main",
                  cidr_block="10.0.0.0/16",
                  enable_dns_hostnames=True,
                  enable_dns_support=True)

# Create an Internet Gateway
igw = aws.ec2.InternetGateway("igw", vpc_id=vpc.id)

# Create a Public Subnet
subnet = aws.ec2.Subnet("subnet",
                         vpc_id=vpc.id,
                         cidr_block="10.0.1.0/24",
                         map_public_ip_on_launch=True,
                         # Specify the availability zone in the eu-central-1 region
                         availability_zone="eu-central-1a")

# Create a Route Table
route_table = aws.ec2.RouteTable("route_table",
                                 vpc_id=vpc.id,
                                 routes=[aws.ec2.RouteTableRouteArgs(
                                     cidr_block="0.0.0.0/0",
                                     gateway_id=igw.id,
                                 )])

# Associate the Route Table with the Subnet
route_table_assoc = aws.ec2.RouteTableAssociation("route_table_assoc",
                                                  subnet_id=subnet.id,
                                                  route_table_id=route_table.id)

# Create a Security Group that allows SSH and HTTP ingress
sec_group = aws.ec2.SecurityGroup("sec_group",
                                  vpc_id=vpc.id,
                                  description="Allow SSH and HTTP inbound access",
                                  ingress=[
                                      aws.ec2.SecurityGroupIngressArgs(
                                          protocol="tcp",
                                          from_port=22,
                                          to_port=22,
                                          cidr_blocks=["0.0.0.0/0"],
                                      ),
                                      aws.ec2.SecurityGroupIngressArgs(
                                          protocol="tcp",
                                          from_port=80,
                                          to_port=80,
                                          cidr_blocks=["0.0.0.0/0"],
                                      ),
                                  ], 
                                  egress=[
                                      aws.ec2.SecurityGroupEgressArgs(
                                            cidr_blocks=["0.0.0.0/0"],
                                            from_port=0,
                                            to_port=0,
                                            protocol="-1", 
                                      )])

# Define the EC2 instance user data to install Docker and run podinfo container
user_data = """
#!/bin/bash
sudo dnf update -y
sudo dnf install docker -y
sudo systemctl start docker
sudo systemctl enable docker
sudo docker run -d -p 80:9898 stefanprodan/podinfo
"""

# Create an EC2 instance with Amazon Linux 2023 AMI in eu-central-1
instance = aws.ec2.Instance("instance",
                            instance_type="t2.micro",
                            # Set the security group defined above
                            vpc_security_group_ids=[sec_group.id],
                            # Replace with the actual AMI ID for Amazon Linux 2023 in eu-central-1
                            ami="ami-0f673487d7e5f89ca",  # placeholder for Amazon Linux 2023 AMI ID
                            subnet_id=subnet.id,
                            user_data=user_data)

# Output the public IP address of the instance
pulumi.export("public_ip", instance.public_ip)
