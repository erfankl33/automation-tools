# Package importing
import os

import gns3fy
from gns3fy.gns3fy import Link, Gns3Connector, Node, Project
import pexpect
import pynetbox as api


"""

__author__ = "Erfan Kamali"
__date__ = "March 4, 2023"


"""


class Gns3:

    switch = "Ethernet switch"
    vpc = "VPCS"
    cloud = "Cloud"

    def __init__(self, url_address, username, password, project_name=None, ios=None, *nodes, ):
        self.url_address = url_address
        self.username = username
        self.password = password
        self.nodes = nodes
        self.ios = ios
        self.project_name = project_name
        # Connect To Api
        self.gns3_server = gns3fy.Gns3Connector(f"http://{self.url_address}", user=self.username, cred=self.password,
                                                verify=False)

    def create_project(self):
        projects_gns = self.gns3_server.get_projects()
        print(projects_gns)
        for i in projects_gns:
            print(i)
            if i['name'] == self.project_name:
                self.lab = Project(name=self.project_name, connector=self.gns3_server)
                self.lab.get()
                self.lab.open()
                print("project opened")
                self.lab.start_nodes()
                return self.lab
            continue

        else:
            self.lab = gns3fy.Project(name=self.project_name, connector=self.gns3_server)
            del self.lab.__pydantic_initialised__
            self.lab.create()
            print("project created")
            return self.lab

    def open_project(self):
        self.lab = Project(name=self.project_name, connector=self.gns3_server)
        self.lab.get()
        projects_gns = self.gns3_server.get_projects()
        for i in projects_gns:
            try:
                if i['name'] == self.project_name:
                    self.lab.open()
                    self.lab.start_nodes()
            except:
                raise AttributeError("there is not your project in list")

    """
        gns.create_nodes(1, "sw", template_type=gns.switch)
        gns.create_nodes(1, "vpc", template_type=gns.vpc)
        gns.create_nodes(1, "cloud", template_type=gns.cloud)
        gns.create_nodes(1, "router", template_type="c7200")
    """

    def create_nodes(self, number, device_name,scenario_name, template_type):
        number_counter = 0
        lab = self.lab
        for i in range(number):
            number_counter += 1
            nodes = gns3fy.Node(
                project_id=lab.project_id,
                connector=self.gns3_server,
                name=f"{scenario_name}{device_name}{number_counter}",
                template=template_type)
            print(f"{device_name}{number_counter}")
            nodes.__dict__.pop("__pydantic_initialised__", None)
            nodes.create()
            nodes.start()
            self.lab.nodes.append(nodes)

    """
    example:
    
        gns.create_link("sw1", "Ethernet1", "cloud1", "Ethernet")
        gns.create_link("sw1", "Ethernet2", "vpc1", "Ethernet0")
        gns.create_link("router1", "FastEthernet0/0", "sw1", "Ethernet3")
        
    """

    def create_link(self, name1, port_number1, name2, port_number2):
        self.lab.get_nodes()
        node_name1 = self.lab.get_node(name=name1)
        node_name2 = self.lab.get_node(name=name2)
        print(node_name1.ports)
        print(node_name2.ports)
        _node1_port = [_p for _p in node_name1.ports if _p["name"] == port_number1][0]
        _node2_port = [_p for _p in node_name2.ports if _p["name"] == port_number2][0]
        nodes1 = [
            dict(node_id=node_name1.node_id, adapter_number=_node1_port["adapter_number"],
                 port_number=_node1_port["port_number"]),
            dict(node_id=node_name2.node_id, adapter_number=_node2_port["adapter_number"],
                 port_number=_node2_port["port_number"])
        ]
        link = Link(project_id=self.lab.project_id, connector=self.gns3_server, nodes=nodes1)
        del link.__pydantic_initialised__
        link.create()

    """
    nodes_info:
        return port number for telnet
        {"vpc1" : "5298"} 
    """
    def nodes_info(self):
        info_dict = {}
        info_node = self.lab.nodes_summary(is_print=False)
        for i in info_node:
            info_dict.update({i[0]: i[2]})
        return info_dict

    """
    input (name , configuration)
    name : node name that we want to configure it
    configuration : configuration commands
    
    example :
        (name=router1, configurations="
        enable
        conf t
        interface fa 0/0
        no shutdown 
        ip address 192.168.11.1 255.255.255.0
        ")
    """

    def configure_node(self, node_name, configurations):
        info_console = self.nodes_info()
        port_number = info_console[node_name]
        child = pexpect.spawn("telnet 192.168.70.234 {} ".format(port_number))
        child.expect(f"{node_name}#")
        for i in configurations.splitlines():
            child.sendline(f"{i}\r")
            child.sendline("")

    def arrange(self):
        project_arrange = Project(name=self.project_name, connector=self.gns3_server)
        project_arrange.arrange_nodes_circular()

    def close_project(self):
        self.lab = Project(name=self.project_name, connector=self.gns3_server)
        self.lab.get()
        self.lab.stop_nodes()
        self.lab.close()

    "Show Name Template for Create Device as Template_type"

    def node_sum(self):
        print("| -- Name -- |")
        for i in self.gns3_server.get_templates():
            print("---------------------------")
            print(i['name'])

    def web(self):
        os.system(f"google-chrome http://192.168.70.234:3080/static/web-ui/server/1/project/{self.lab.project_id}")

    def inventory(self, device_name, ipaddress):
        import pynetbox as api

        # Connect to NetBox API
        nb = api.api(url='http://192.168.70.238:8000', token='8bdfa7752d72abedaeed3b52c934e4726b279aa2')

        # Define device information
        device_name = device_name
        device_site = 'GNS3'
        device_role = 'GNS3'
        device_type = 'GNS3'
        ip_address = ipaddress
        interface_name = 'eth0'

        # Get site ID
        site = nb.dcim.sites.get(name=device_site)
        device_role = nb.dcim.device_roles.get(name=device_role)
        device_type = nb.dcim.device_types.get(model=device_type)

        # Create device in NetBox
        device = nb.dcim.devices.create(
            name=device_name,
            site=site.id,
            device_role=device_role.id,
            device_type=device_type.id,
            description=ip_address

        )

        # Get device ID
        device = nb.dcim.devices.get(name=device_name)

        # Create interface and assign IP address
        interface = nb.dcim.interfaces.create(
            device=device.id,
            type='100base-tx',
            name=interface_name,
            enabled=True,
            mtu=1500,
            description=ip_address,
            ip_address=ip_address
        )

        ip = nb.ipam.ip_addresses.create(
            address=ip_address,
            status='active',
            interface=interface.id
        )

        # Print device information
        print(f"Created device: {device_name} (ID: {device.id})")

        # Print interface information
        print(f"Created interface: {interface.name} (ID: {interface.id}) with IP address: {ip.address}")
