from dataclasses import dataclass
from typing import Optional, Tuple, Dict, Any, Iterable
from xsdata.formats.dataclass.parsers import XmlParser
from xsdata.formats.dataclass.context import XmlContext

from sgr_library.data_classes.ei_modbus import SgrModbusDeviceDescriptionType
from sgr_library.data_classes.ei_modbus.sgr_modbus_eidevice_frame import SgrModbusDataPointsFrameType
from sgr_library.modbus_connect import ModbusConnect


def get_address(root) -> str:
    """
    :return: string with ip address from xml file.
    """
    address = ''
    address += str(root.modbus_interface_desc.trsp_srv_modbus_tcpout_of_box.address.ip_v4n1)
    address += '.'
    address += str(root.modbus_interface_desc.trsp_srv_modbus_tcpout_of_box.address.ip_v4n2)
    address += '.'
    address += str(root.modbus_interface_desc.trsp_srv_modbus_tcpout_of_box.address.ip_v4n3)
    address += '.'
    address += str(root.modbus_interface_desc.trsp_srv_modbus_tcpout_of_box.address.ip_v4n4)
    return address

def get_port(root) -> str:
    """
    :return: string with port from xml file.
    """
    return(str(root.modbus_interface_desc.trsp_srv_modbus_tcpout_of_box.port))

def find_dp(root, fp_name, dp_name) -> SgrModbusDataPointsFrameType:
    """
    Search datapoint
    """
    for fp in root.fp_list_element:
            if fp_name == fp.functional_profile.profile_name:
                #Secondly we filter the datpoint name
                for dp in fp.dp_list_element:
                    if dp_name == dp.data_point[0].datapoint_name:
                        return dp
    return None

class ModbusInterface: 

    def __init__(self, xml_file) -> None:
        """
        Creates a connection from xml file data.
        Parses the xml file with xsdata library.
        """
        interface_file = xml_file
        parser = XmlParser(context=XmlContext())
        self.root = parser.parse(interface_file, SgrModbusDeviceDescriptionType)
        self.ip = get_address(self.root)
        self.port = get_port(self.root)
        self.client = ModbusConnect(self.ip, self.port)

    def datapoint_info(self, fp_name, dp_name) -> Tuple[int, int, int, str, str, int, int]:
        """
        Returns datapoint information.
        """
        dp = find_dp(self.root, fp_name, dp_name)
        if dp:
            # We fill the searched datapoint information into variables.
            address = dp.modbus_data_point[0].modbus_first_register_reference.addr
            size = dp.modbus_data_point[0].dp_size_nr_registers
            bitrank = dp.modbus_data_point[0].modbus_first_register_reference.bit_rank
            register_type = dp.modbus_data_point[0].modbus_first_register_reference.register_type.value
            unit = dp.data_point[0].unit.value
            multiplicator = dp.dp_mb_attr_reference[0].modbus_attr[0].scaling_by_mul_pwr.multiplicator
            power_of = dp.dp_mb_attr_reference[0].modbus_attr[0].scaling_by_mul_pwr.powerof10
            return (address, size, bitrank, register_type, unit, multiplicator, power_of)
        print('Requested datapoint not found in xml file')
        #TODO raise exception: datapoint not found.


    def getval(self, fp_name, dp_name) -> float:
        """
        Reads datapoint value
        """
        datapoint_info = self.datapoint_info(fp_name, dp_name)
        address = int(datapoint_info[0])
        size = int(datapoint_info[1])
        reg_type = 'FLOAT32' #TODO Regtype from xml file...
        return self.client.value_decoder(address, size, reg_type)


    def setval(self, fp_name, dp_name, value) -> None:
        """
        Writes datapoint value
        """
        datapoint_info = self.datapoint_info(fp_name, dp_name)
        address = int(datapoint_info[0])
        reg_type = 'INT32u' #TODO Regtype from xml file...
        self.client.value_encoder(address, value, reg_type)


if __name__ == "__main__":

    print('start')
    interface_file = 'SGr_04_0016_xxxx_ABBMeterV0.2.1.xml'
    a = ModbusInterface(interface_file)
    #a.setval('ActiveEnerBalanceAC', 'ActiveImportAC', 9000)
    print(a.getval('ActiveEnerBalanceAC', 'ActiveImportAC'))

    