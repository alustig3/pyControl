from pyControl.hardware import Port


class Breakout_portenta:
    def __init__(self):
        # Inputs and outputs.
        self.port_1 = Port(
            DIO_A="PJ8",
            DIO_B="PJ9",
            DIO_C="PI4",
            POW_A="A2",
            POW_B="A3",
            UART=8,
        )

        self.port_2 = Port(
            DIO_A="PH11",
            DIO_B="PH12",
            DIO_C="PH14",
            POW_A="A0",
            POW_B="A1",
            I2C=4,
        )

        self.port_3 = Port(
            DIO_A="PG14",
            DIO_B="PG9",
            DIO_C="PH10",
            POW_A="PG7",
            POW_B="PJ11",
            UART=6,
        )

        self.port_4 = Port(
            DIO_A="PC3",
            DIO_B="PC2",
            DIO_C="PI1",
            POW_A="PD6",
            POW_B="PI14",
        )

        self.port_5 = Port(
            DIO_A="PH7",
            DIO_B="PH8",
            DIO_C="PH9",
            POW_A="PI6",
            POW_B="PA8",
            I2C=3,
        )

        self.port_6 = Port(
            DIO_A="PA0",
            DIO_B="PI9",
            DIO_C="PI0",
            POW_A="PI5",
            POW_B="PI7",
            UART=4,
        )

        self.port_7 = Port(
            DIO_A="PA9",
            DIO_B="PA10",
            DIO_C="PC12",
            POW_A="PA4",
            POW_B="PA6",
            UART=1,
        )

        self.port_8 = Port(
            DIO_A="PB6",
            DIO_B="PB7",
            DIO_C="PC14",
            POW_A="PJ10",
            POW_B="PH6",
            I2C=1,
        )

        self.port_9 = Port(
            DIO_A="PH13",
            DIO_B="PB8",
            DIO_C="PD4",
            POW_A="PD7",
            POW_B="PI15",
        )

        self.port_10 = Port(
            DIO_A="PC6",
            DIO_B="PC7",
            DIO_C="PJ6",
            POW_A="PB15",
            POW_B="PB14",
        )

        self.port_11 = Port(
            DIO_A="PA12",
            DIO_B="PA11",
            DIO_C="PI10",
            POW_A="PA13",
            POW_B="PB4",
        )

        self.port_12 = Port(
            DIO_A="PE2",
            DIO_B="PB2",
            DIO_C="PD5",
            POW_A="PB3",
            POW_B="PA14",
        )

        self.LED_red = "LED_RED"
        self.LED_green = "LED_GREEN"
        self.LED_blue = "LED_BLUE"
