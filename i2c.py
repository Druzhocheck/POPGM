import smbus
import time
import subprocess

class ADAU1761Programmer:
    # Инициализация шины и адреса DSP
    def __init__(self, i2c_bus=5, i2c_address=0x38):
        self.bus = smbus.SMBus(i2c_bus)
        self.address = i2c_address
        
    # Метод записи блоков данных в адреса   
    def write_register_block(self, address, data):
        # Преобразуем адрес в 2 байта (старший и младший)
        # Т.е если адрес 0x4002, то 0x40 старший, 0x02 младший
        
        addr_high = (address >> 8) & 0xFF
        addr_low = address & 0xFF
        if not isinstance(data, list):
            self.bus.write_byte_data(self.address, addr_high, data)
        time.sleep(0.001)
        return True

    # Метод задержки между запясями    
    def write_delay(self, delay_ms):
        time.sleep(delay_ms / 1000.0)
    
    # Загрузка начальной конфигурации
    def default_download(self):
        # Регистр запуска DSP (R0_DSP_RUN_REGISTER_IC_1_Default)
        self.write_register_block(0xF400, 0x00)
        
        # Регистр управления тактированием (R1_CLKCTRLREGISTER_IC_1_Default)
        self.write_register_block(0x4000, 0x01) 
        
        # Регистр управления PLL (R2_PLLCRLREGISTER_IC_1_Default)
        self.write_register_block(0x4002, [0x00, 0xFD, 0x00, 0x0C, 0x20, 0x03])
        
        # Задержка (R3_DELAY_IC_1_Default)
        self.write_delay(100)
        
        # Регистры управления последовательным портом (R4_SERIAL_PORT_CONTROL_REGISTERS_IC_1_Default)
        self.write_register_block(0x4015, [0x00, 0x00])
        
        # Регистры управления ALC (R5_ALC_CONTROL_REGISTERS_IC_1_Default)
        self.write_register_block(0x4011, [0xC0, 0x00, 0x00, 0x00])
        
        # Регистр управления микрофоном (R6_MICCTRLREGISTER_IC_1_Default)
        self.write_register_block(0x4008, 0x00)
        
        # Регистры пути входного сигнала записи (R7_RECORD_INPUT_SIGNAL_PATH_REGISTERS_IC_1_Default)
        self.write_register_block(0x4009, [0x00, 0x01, 0x08, 0x01, 0x08, 0x43, 0x43, 0x00])
        
        # Регистры управления ADC (R8_ADC_CONTROL_REGISTERS_IC_1_Default)
        self.write_register_block(0x4019, [0x13, 0x00, 0x00])

        # Регистры пути выходного сигнала воспроизведения
        self.write_register_block(0x401C, [0x00, 0x00, 0x00, 0x00, 0x04, 0x10, 0x00, 0xE4, 0xE4, 0xFC, 0xFC, 0xFD, 0x0E, 0x00])  # R9_PLAYBACK_OUTPUT_SIGNAL_PATH_REGISTERS_IC_1_Default
        
        # Регистры управления преобразователем (R10_CONVERTER_CONTROL_REGISTERS_IC_1_Default)
        self.write_register_block(0x4017, [0x1B, 0x00])
        
        # Регистры управления DAC (R11_DAC_CONTROL_REGISTERS_IC_1_Default)
        self.write_register_block(0x402A, [0x00, 0x00, 0x00])
        
        # Регистры управления выводами последовательного порта (R12_SERIAL_PORT_PAD_CONTROL_REGISTERS_IC_1_Default)
        self.write_register_block(0x402D, 0xAA)
        
        # Регистры управления выводами порта связи (R13_COMMUNICATION_PORT_PAD_CONTROL_REGISTERS_IC_1_Default)
        self.write_register_block(0x402F, [0x00, 0x01])
        
        # Регистр управления детектированием джека (R14_JACKREGISTER_IC_1_Default)
        self.write_register_block(0x4031, 0x08)
        
        # Регистр включения DSP (R15_DSP_ENABLE_REGISTER_IC_1_Default)
        self.write_register_block(0x40F5, 0x01)
        
        # Регистры CRC (R16_CRC_REGISTERS_IC_1_Default)
        self.write_register_block(0x40C0, [0x6D, 0x08, 0x24, 0x7F, 0x00])

        # Регистры GPIO (R17_GPIO_REGISTERS_IC_1_Default)
        self.write_register_block(0x40C6, [0x00, 0x00, 0x00, 0x00])
        
        # Регистры non-modulo RAM (R18_NON_MODULO_REGISTERS_IC_1_Default)
        self.write_register_block(0x40E9, [0x10, 0x00])
        
        # Регистры watchdog (R19_WATCHDOG_REGISTERS_IC_1_Default)
        self.write_register_block(0x40D0, [0x00, 0x00, 0x00, 0x00, 0x00])
        
        # Регистр настройки частоты дискретизации (R20_SAMPLE_RATE_SETTING_IC_1_Default)
        self.write_register_block(0x40EB, 0x7F)
        
        # Регистр матрицы маршрутизации входов (R21_ROUTING_MATRIX_INPUTS_IC_1_Default)
        self.write_register_block(0x40F2, 0x00)
        
        # Регистр матрицы маршрутизации выходов (R22_ROUTING_MATRIX_OUTPUTS_IC_1_Default)
        self.write_register_block(0x40F3, 0x01)
        
        # Регистр конфигурации последовательных данных/выводов GPIO (R23_SERIAL_DATAGPIO_PIN_CONFIG_IC_1_Default)
        self.write_register_block(0x40F4, 0x00)
        
        # Регистр режимов slew DSP (R24_DSP_SLEW_MODES_IC_1_Default)
        self.write_register_block(0x40F7, 0x00)
        
        # Регистр настройки частоты дискретизации последовательного порта (R25_SERIAL_PORT_SAMPLE_RATE_SETTING_IC_1_Default)
        self.write_register_block(0x40F8, 0x03)

        # Регистры включения тактирования (R26_CLOCK_ENABLE_REGISTERS_IC_1_Default)
        self.write_register_block(0x40F9, [0x1B, 0x03])
        
        # Загрузка программы DSP (PROGRAM_ADDR_IC_1)
        program_data = [
            0x00, 0x00, 0x00, 0x00, 0x00, 0xFE, 0xE0, 0x00, 0x00, 0x00, 
            0xFF, 0x34, 0x00, 0x00, 0x00, 0xFF, 0x2C, 0x00, 0x00, 0x00, 
            0xFF, 0x54, 0x00, 0x00, 0x00, 0xFF, 0x5C, 0x00, 0x00, 0x00, 
            0xFF, 0xF5, 0x08, 0x20, 0x00, 0xFF, 0x38, 0x00, 0x00, 0x00, 
            0xFF, 0x80, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0xFE, 0xE8, 0x0C, 0x00, 0x00, 
            0xFE, 0x30, 0x00, 0xE2, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0xFF, 0xE8, 0x07, 0x20, 0x08, 
            0x00, 0x00, 0x06, 0xA0, 0x00, 0xFF, 0xE0, 0x00, 0xC0, 0x00, 
            0xFF, 0x80, 0x07, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0xFF, 0x00, 0x00, 0x00, 0x00, 0xFE, 0xC0, 0x22, 0x00, 0x27, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0xFE, 0xE8, 0x1E, 0x00, 0x00, 
            0xFF, 0xE8, 0x01, 0x20, 0x00, 0xFF, 0xD8, 0x01, 0x03, 0x00, 
            0x00, 0x07, 0xC6, 0x00, 0x00, 0xFF, 0x08, 0x00, 0x00, 0x00, 
            0xFF, 0xF4, 0x00, 0x20, 0x00, 0xFF, 0xD8, 0x07, 0x02, 0x00, 
            0xFD, 0xA5, 0x08, 0x20, 0x00, 0x00, 0x00, 0x00, 0xE2, 0x00, 
            0xFD, 0xAD, 0x08, 0x20, 0x00, 0x00, 0x08, 0x00, 0xE2, 0x00, 
            0x00, 0x05, 0x08, 0x20, 0x00, 0xFD, 0x60, 0x00, 0xE2, 0x00, 
            0x00, 0x0D, 0x08, 0x20, 0x00, 0xFD, 0x68, 0x00, 0xE2, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0xFE, 0x30, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0xFE, 0xC0, 0x0F, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00
        ]
        self.write_register_block(0x0800, program_data)  
        
        # Загрузка параметров DSP (PARAM_ADDR_IC_1)
        param_data = [
            0x00, 0x00, 0x10, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 
            0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00, 0x00
        ]
        self.write_register_block(0x0000, param_data)
        
        # Включение DSP (R29_DSP_RUN_REGISTER_IC_1_Default)
        self.write_register_block(0x40F6, 0x01)
        
        # Регистр управления dejitter (R30_DEJITTER_REGISTER_CONTROL_IC_1_Default)
        self.write_register_block(0x4036, 0x00)
        # (R31_DEJITTER_REGISTER_CONTROL_IC_1_Default)
        self.write_register_block(0x4036, 0x03)
        
        print("Конфигурация DSP успешно завершена")

if __name__ == "__main__":
    try:
        # print("Инициализация программирования ADAU1761...")
        programmer = ADAU1761Programmer(i2c_bus=5, i2c_address=0x38)
        print("Запуск процесса конфигурации...")
        programmer.default_download()
        print("ADAU1761 успешно сконфигурирован")
    except Exception as e:
        print(f"Ошибка: {e}")