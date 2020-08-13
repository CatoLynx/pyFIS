from splitflap.display import SplitFlapDisplay, TextField, CustomMapField
from splitflap.krone import KroneFBMController

MAP_TRAIN_TYPE = {
    32: "",
    33: "EC",
    34: "IC",
    35: "ICE",
    36: "ICT",
    37: "IR",
    38: "AZ",
    39: "D",
    40: "RE",
    41: "RB",
    42: "SE",
    43: "EN",
    44: "NZ",
    45: "UEx",
    46: "CNL",
    47: "",
    48: "",
    49: "IRE",
    50: "CB",
}

class ExampleDisplay(SplitFlapDisplay):
    train_type = CustomMapField(MAP_TRAIN_TYPE, start_address=1, x=0, y=0, module_width=3, module_height=1)
    train_number = TextField(start_address=2, length=5, x=3, y=0, module_width=1, module_height=1)
    destination = TextField(start_address=7, length=8, x=0, y=1, module_width=2, module_height=2)
    info_text = TextField(start_address=15, length=16, x=0, y=3, module_width=1, module_height=1)


def main():
    controller = KroneFBMController("/dev/ttyS0")
    display = ExampleDisplay(controller)
    display.train_type.set("ICE")
    display.train_number.set("524")
    display.destination.set("Dortmund")
    display.info_text.set("ca 10 Min später")
    display.update()
    print(display.render_ascii())


if __name__ == "__main__":
    main()
