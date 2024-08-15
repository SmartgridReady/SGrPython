from enum import Enum
from sgr_library.modbus_interface import SgrModbusInterface
from sgr_library.driver.restapi_client_async import SgrRestInterface
from sgr_library.modbusRTU_interface_async import SgrModbusRtuInterface
from typing import Callable, Tuple, Dict

import re
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser
import configparser
from xsdata.formats.dataclass.context import XmlContext
from xsdata.formats.dataclass.parsers import XmlParser

from sgrspecification.product import DeviceFrame

class SGrConfiguration(Enum):
    UNKNOWN = 1
    STRING = 2
    FILE = 3


class SGrDeviceProtocol(Enum):
    MODBUS_RTU = 0
    MODBUS_TPC = 1
    RESTAPI = 2
    GENERIC = 3
    CONTACT = 4

device_builders: Dict[SGrDeviceProtocol, Callable[
    [DeviceFrame, configparser.ConfigParser], SgrRestInterface | SgrModbusInterface | SgrModbusRtuInterface]
] = {
    SGrDeviceProtocol.MODBUS_TPC: lambda frame, _: SgrModbusInterface(frame),
    SGrDeviceProtocol.MODBUS_RTU: lambda frame, _: SgrModbusRtuInterface(frame),
    SGrDeviceProtocol.RESTAPI: lambda frame, config: SgrRestInterface(frame, config),
    # SGrDeviceProtocol.GENERIC: lambda frame, config: SgrModbusInterface(frame),
    # SGrDeviceProtocol.CONTACT: lambda frame, config: SgrModbusInterface(frame)
}

class DeviceBuilder:

    def __init__(self):
        self._value: str | None = None
        self._config_value: str | Dict | None = None
        self._type: SGrConfiguration = SGrConfiguration.UNKNOWN
        self._config_type: SGrConfiguration = SGrConfiguration.UNKNOWN


    def build(self) -> SgrRestInterface | SgrModbusInterface | SgrModbusRtuInterface:
        spec, config = self.replace_variables()
        xml = self.string_loader()
        protocol = self.resolve_protocol(xml)
        return device_builders[protocol](xml, config)

    def resolve_protocol(self, frame: DeviceFrame) -> SGrDeviceProtocol:
        if frame.interface_list is None:
            raise Exception("unsuproted device interface")
        if frame.interface_list.rest_api_interface:
            return SGrDeviceProtocol.RESTAPI
        elif frame.interface_list.modbus_interface is not None and frame.interface_list.modbus_interface.modbus_interface_description.modbus_rtu:
            return SGrDeviceProtocol.MODBUS_RTU
        elif frame.interface_list.modbus_interface is not None and frame.interface_list.modbus_interface.modbus_interface_description.modbus_tcp:
            return SGrDeviceProtocol.MODBUS_TPC
        elif frame.interface_list.contact_interface:
            return SGrDeviceProtocol.CONTACT
        else:
            return SGrDeviceProtocol.GENERIC

    def string_loader(self) -> DeviceFrame:
        parser = XmlParser(context=XmlContext())
        if self._value is None:
            raise Exception("missing specifcation")
        return parser.from_string(self._value, DeviceFrame)


    def file_loader(self) -> DeviceFrame:
        parser = XmlParser(context=XmlContext())
        return parser.parse(self._value, DeviceFrame)

    def get_spec_content(self) -> str:
        if self._value is None:
            raise Exception("No spec configured")
        if self._type == SGrConfiguration.FILE:
            try:
                input_file = open(self._value)
                return input_file.read()
            except:
                raise Exception("Invalid spec file path")
        elif self._type == SGrConfiguration.STRING:
            return self._value
        return ""

    def xml_file_path(self, file_path: str):
        self._value = file_path
        self._type = SGrConfiguration.FILE
        return self

    def xml_string(self, xml: str):
        self._value = xml
        self._type = SGrConfiguration.STRING
        return self

    def config_file_path(self, file_path: str):
        self._config_type = SGrConfiguration.FILE
        self._config_value = file_path
        return self

    def config(self, config: Dict):
        self._config_type = SGrConfiguration.STRING
        self._config_value = config
        return self

    def replace_variables(self) -> Tuple[str, configparser.ConfigParser]:
        config = configparser.ConfigParser()
        params = self._config_value if self._config_value is not None else {}
        if self._config_type is SGrConfiguration.FILE:
            config.read(params)
        elif self._config_type is SGrConfiguration.STRING:
            params = params if not isinstance(params, str) else {}
            config.read_dict(params)
        spec = self.get_spec_content()
        for section_name, section in config.items():
            for param_name in section:
                pattern = re.compile(r'{{' + param_name + r'}}')
                spec = pattern.sub(config.get(section_name, param_name), spec)

        return spec, config
