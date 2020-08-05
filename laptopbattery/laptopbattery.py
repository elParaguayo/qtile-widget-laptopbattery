import pydbus

from libqtile.widget import base
from libqtile import bar, images

UPOWER_INTERFACE = ".UPower"


class LaptopBatteryWidget(base._Widget):

    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("battery_height", 10, "Height of battery icon"),
        ("battery_width", 20, "Size of battery icon"),
        ("battery_name", None, "Battery name. None = all batteries"),
        ("border_charge_colour", "8888ff", "Border colour when charging."),
        ("border_colour", "dbdbe0", "Border colour when discharging."),
        ("border_critical_colour", "cc0000", "Border colour when battery low."),
        ("fill_normal", "dbdbe0", "Fill when normal"),
        ("fill_low", "aa00aa", "Fill colour when battery low"),
        ("fill_critical", "cc0000", "Fill when critically low"),
        ("margin", 2, "Margin on sides of widget"),
        ("spacing", 5, "Space between batteries"),
        ("percentage_low", 0.20, "Low level threshold."),
        ("percentage_critical", 0.10, "Critical level threshold."),
    ]

    def __init__(self, **config):
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(LaptopBatteryWidget.defaults)

    def _configure(self, qtile, bar):
        base._Widget._configure(self, qtile, bar)

        # Set up connection to DBus
        self.bus = pydbus.SystemBus()
        self.upower = self.bus.get(UPOWER_INTERFACE)

        # Listen for property change (this is triggered when laptop is
        # (dis)connected to a power supply)
        self.upower.onPropertiesChanged = self.upower_change

        # Define colours
        self.colours = [
          (self.percentage_critical, self.fill_critical),
          (self.percentage_low, self.fill_low),
          (100, self.fill_normal)
        ]
        self.borders = {True: self.border_charge_colour,
                        False: self.border_colour}

        # Get battery details from DBus
        self.find_batteries()

        # Is laptop charging?
        self.charging = not self.upower.OnBattery

        self.update()

    def calculate_length(self):
        num_batteries = len(self.batteries)
        if num_batteries:
            length = ((self.margin * 2) +
                     (self.spacing * (num_batteries -1)) +
                     (self.battery_width * num_batteries))
            return length
        else:
            return 0

    def find_batteries(self, *args):
        # Get all UPower devices that are named "battery"
        batteries = [b for b in self.upower.EnumerateDevices()
                                  if "battery" in b]

        # Get DBus object for each battery
        self.batteries = [self.bus.get(UPOWER_INTERFACE, b) for b in batteries]

        # If user only wants named battery, get it here
        if self.battery_name:
            self.batteries = [b for b in self.batteries
                              if b.NativePath == self.battery_name]

        # Listen for change signals on DBus
        for battery in self.batteries:
            battery.onPropertiesChanged = self.battery_change

    def upower_change(self, sender, props, invalidated):
        # Update the charging status
        self.charging = not self.upower.OnBattery

        # Redraw the widget
        self.update()

    def battery_change(self, sender, props, invalidated):
        # The batteries are polled every 2 mins by DBus so let's just update
        # when we get any signal
        self.update()

    def update(self):
        # Remove background
        self.drawer.clear(self.background or self.bar.background)

        # Define an offset for widgets
        offset = self.margin

        # Work out top of battery
        top_margin = (self.bar.height - self.battery_height) / 2

        # Loop over each battery
        for battery in self.batteries:

            # Get battery energy level
            percentage = battery.Percentage / 100.0

            # Get the appropriate fill colour
            # This finds the first value in self_colours which is greater than
            # the current battery level and returns the colour string
            fill = next(x[1] for x in self.colours if percentage <= x[0])

            # Choose border colour
            if (percentage <= self.percentage_critical) and not self.charging:
                border = self.border_critical_colour
            else:
                border = self.borders[self.charging]

            # Draw the border
            self.drawer._rounded_rect(
                offset,
                top_margin,
                self.battery_width,
                self.battery_height,
                1
            )

            self.drawer.set_source_rgb(border)
            self.drawer.ctx.stroke()

            # Work out size of bar inside icon
            fill_width = 2 + (self.battery_width - 6) * percentage

            # Draw the filling of the battery
            self.drawer._rounded_rect(
                offset + 2,
                top_margin + 2,
                fill_width,
                (self.battery_height - 4),
                0)
            self.drawer.set_source_rgb(fill)
            self.drawer.ctx.fill()

            # Increase offset for next battery
            offset = offset + self.spacing + self.battery_width

        # Redraw the bar
        self.bar.draw()

    def draw(self):
        self.drawer.draw(offsetx=self.offset, width=self.length)
