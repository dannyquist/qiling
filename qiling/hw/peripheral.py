#!/usr/bin/env python3
# 
# Cross Platform and Multi Architecture Advanced Binary Emulation Framework
#

import ctypes
from typing import List, Tuple

from qiling.core import Qiling


class QlPeripheral:
    class Type(ctypes.Structure):
        """ Define the reigister fields of peripheral.

            Example:
                fields_ = [
                    ('SR'  , ctypes.c_uint32),
                    ('DR'  , ctypes.c_uint32),
                    ('BRR' , ctypes.c_uint32),
                    ('CR1' , ctypes.c_uint32),
                    ('CR2' , ctypes.c_uint32),
                    ('CR3' , ctypes.c_uint32),
                    ('GTPR', ctypes.c_uint32),
                ]
        """        
        _fields_ = []
    
    def __init__(self, ql: Qiling, label: str):
        self.ql = ql
        self.label = label
        self.struct = type(self).Type

    def step(self):
        """ Update the state of the peripheral, 
            called after each instruction is executed
        """        
        pass
    
    @staticmethod
    def read_debug(read):
        def read_wrapper(self, offset: int, size: int) -> int:
            retval = read(self, offset, size)
            self.ql.log.debug(f'[{self.label.upper()}] [R] {self.find_field(offset, size):10s} = {hex(retval)}')
            return retval
        
        return read_wrapper

    @staticmethod
    def write_debug(write):
        def write_wrapper(self, offset: int, size: int, value: int):
            field, extra = self.find_field(offset, size), ''
            if field.startswith('DR') and value <= 255:
                extra = f'({repr(chr(value))})'

            self.ql.log.debug(f'[{self.label.upper()}] [W] {field:10s} = {hex(value)} {extra}')
            return write(self, offset, size, value)

        return write_wrapper

    def read(self, offset: int, size: int) -> int:
        return 0

    def write(self, offset: int, size: int, value: int):
        pass

    def in_field(self, field, offset: int, size: int) -> bool:
        return field.offset <= offset and offset + size <= field.offset + field.size

    def find_field(self, offset: int, size: int) -> str:
        """ Return field names in interval [offset: offset + size],
            the function is designed for logging and debugging.

        Returns:
            str: Field name
        """

        field_list = []
        for name, _ in self.struct._fields_:
            field = getattr(self.struct, name)
            
            lbound = max(0, offset - field.offset)
            ubound = min(offset + size  - field.offset, field.size)
            if lbound < ubound:
                if lbound == 0 and ubound == field.size:
                    field_list.append(name)
                else:
                    field_list.append(f'{name}[{lbound}:{ubound}]')
                
        return ','.join(field_list)

    @property
    def region(self) -> List[Tuple]:
        """Get the memory intervals occupyied by peripheral (base address = 0x0).

        Returns:
            List[Tuple]: Memory intervals occupyied by peripheral
        """
        return [(0, ctypes.sizeof(self.struct))]

    @property
    def size(self) -> int:
        """Calculate the memory size occupyied by peripheral.

        Returns:
            int: Size
        """        
        return sum(rbound-lbound for lbound, rbound in self.region)

    @property
    def base(self) -> int:
        """Get the base address from QlHwManager.

        Returns:
            int: Peripheral's base address
        """        
        return self.ql.hw.region[self.label][0][0]
