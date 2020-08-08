import pydbus

from libqtile.widget import base
from libqtile import bar, images
from libqtile.log_utils import logger

UPOWER_INTERFACE = ".UPower"


class LaptopBatteryWidget(base._Widget):

    orientations = base.ORIENTATION_HORIZONTAL
    defaults = [
        ("font", "sans", "Default font"),
        ("fontsize", None, "Font size"),
        ("font_colour", "ffffff", "Font colour for information text"),
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
        ("text_charging", "({percentage:.0f}%) {ttf} until fully charged",
                          "Text to display when charging."),
        ("text_discharging", "({percentage:.0f}%) {tte} until empty",
                          "Text to display when on battery."),
        ("text_displaytime", 5, "Time for text to remain before hiding"),
    ]

    def __init__(self, **config):
        base._Widget.__init__(self, bar.CALCULATED, **config)
        self.add_defaults(LaptopBatteryWidget.defaults)

        # Initial variables to hide text
        self.show_text = False
        self.hide_timer = None

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

    def max_text_length(self):
        # Generate text string based on status
        if self.charging:
            text = self.text_charging.format(percentage=100, ttf="99:99")
        else:
            text = self.text_discharging.format(percentage=100, tte="99:99")

        # Calculate width of text
        width, _ = self.drawer.max_layout_size(
            [text],
            self.font,
            self.fontsize
        )

        return width

    def calculate_length(self):
        # Start with zero width and we'll add to it
        bar_length = 0

        # We can use maths to simplify if more than one battery
        num_batteries = len(self.batteries)

        if num_batteries:
            # Icon widths
            length = ((self.margin * 2) +
                     (self.spacing * (num_batteries -1)) +
                     (self.battery_width * num_batteries))

            bar_length += length

            # Add text width if it's being displayed
            if self.show_text:

                bar_length += (self.max_text_length() +
                              self.spacing) * num_batteries

        return bar_length

    def find_batteries(self, *args):
        # Get all UPower devices that are named "battery"
        batteries = [b for b in self.upower.EnumerateDevices()
                                  if "battery" in b]

        if not batteries:
            logger.warning("No batteries found. No icons will be displayed.")

        # Get DBus object for each battery
        self.batteries = [self.bus.get(UPOWER_INTERFACE, b) for b in batteries]

        # If user only wants named battery, get it here
        if self.battery_name:
            self.batteries = [b for b in self.batteries
                              if b.NativePath == self.battery_name]

            if not self.batteries:
                logger.warning("No battery found matching {}.".format(self.battery_name))

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

            if self.show_text:

                percentage = battery.Percentage

                # Generate text based on status and format time-to-full or
                # time-to-empty
                if self.charging:
                    ttf = self.secs_to_hm(battery.TimeToFull)
                    text = self.text_charging.format(percentage=percentage,
                                                     ttf=ttf)
                else:
                    tte = self.secs_to_hm(battery.TimeToEmpty)
                    text = self.text_discharging.format(percentage=percentage,
                                                        tte=tte)

                # Create a text box
                layout = self.drawer.textlayout(text,
                                                self.font_colour,
                                                self.font,
                                                self.fontsize,
                                                None,
                                                wrap=False)

                # We want to centre this vertically
                y_offset = (self.bar.height - layout.height) / 2

                # Set the layout as wide as the widget so text is centred
                layout.width = self.max_text_length()

                # Draw it
                layout.draw(offset, y_offset)

                # Increase the offset
                offset += layout.width

        # Redraw the bar
        self.bar.draw()

    def secs_to_hm(self, secs):
        # Basic maths to convert seconds to h:mm format
        m, _ = divmod(secs, 60)
        h, m = divmod(m, 60)

        # Need to mke sure minutes are zero padded in case single digit
        return ("{}:{:02d}".format(h, m))

    def draw(self):
        self.drawer.draw(offsetx=self.offset, width=self.length)

    def button_press(self, x, y, button):
        # Check if it's a right click and, if so, toggle textt
        if button == 1:
            if not self.show_text:
                self.show_text = True

                # Start a timer to hide the text
                self.hide_timer = self.timeout_add(self.text_displaytime,
                                                   self.hide)
            else:
                self.show_text = False

                # Cancel the timer as no need for it if text is hidden already
                if self.hide_timer:
                    self.hide_timer.cancel()

            self.update()

    def hide(self):
        # Self-explanatory!
        self.show_text = False
        self.update()
