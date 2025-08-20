#!/usr/bin/env python3
"""
Professional Time Calculator for Linux
A comprehensive GUI application for time calculations with date support and scalar multiplication
Includes system tray integration and custom icon
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime, timedelta
from PIL import Image, ImageDraw, ImageTk
import threading
import io
import base64

# Try to import pystray for system tray support
try:
    import pystray
    from pystray import MenuItem as item
    TRAY_AVAILABLE = True
except ImportError:
    TRAY_AVAILABLE = False
    print("pystray not available. Install with: pip install pystray Pillow")
    print("System tray features will be disabled.")


class TimeCalculator:
    def __init__(self, root):
        self.root = root
        self.tray_icon = None
        self.is_hidden = False
        self.setup_window()
        self.create_icon()
        self.setup_styles()
        self.create_interface()
        self.bind_shortcuts()
        self.setup_tray()

    def create_icon(self):
        """Create a custom clock icon programmatically"""
        # Create a 64x64 icon
        size = 64
        image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw clock face (circle)
        margin = 4
        circle_bbox = [margin, margin, size-margin, size-margin]
        draw.ellipse(circle_bbox, fill='#2c3e50', outline='#34495e', width=2)
        
        # Draw clock hands
        center = size // 2
        
        # Hour hand (pointing to 3 o'clock for calculator theme)
        hour_end_x = center + 12
        hour_end_y = center
        draw.line([center, center, hour_end_x, hour_end_y], fill='white', width=4)
        
        # Minute hand (pointing to 12)
        minute_end_x = center
        minute_end_y = center - 16
        draw.line([center, center, minute_end_x, minute_end_y], fill='white', width=3)
        
        # Draw hour markers
        for hour in range(12):
            angle = hour * 30  # 360/12 = 30 degrees per hour
            import math
            angle_rad = math.radians(angle - 90)  # -90 to start at 12 o'clock
            
            # Outer point
            outer_x = center + 20 * math.cos(angle_rad)
            outer_y = center + 20 * math.sin(angle_rad)
            
            # Inner point
            inner_x = center + 16 * math.cos(angle_rad)
            inner_y = center + 16 * math.sin(angle_rad)
            
            draw.line([inner_x, inner_y, outer_x, outer_y], fill='white', width=2)
        
        # Center dot
        dot_size = 3
        draw.ellipse([center-dot_size, center-dot_size, center+dot_size, center+dot_size], 
                    fill='white')
        
        # Add small calculator symbol in corner
        calc_size = 12
        calc_x = size - calc_size - 4
        calc_y = size - calc_size - 4
        draw.rectangle([calc_x, calc_y, calc_x + calc_size, calc_y + calc_size], 
                      fill='#3498db', outline='#2980b9')
        
        # Add + symbol on calculator
        plus_x = calc_x + calc_size // 2
        plus_y = calc_y + calc_size // 2
        draw.line([plus_x - 3, plus_y, plus_x + 3, plus_y], fill='white', width=2)
        draw.line([plus_x, plus_y - 3, plus_x, plus_y + 3], fill='white', width=2)
        
        # Convert to PhotoImage for tkinter
        self.window_icon = ImageTk.PhotoImage(image)
        
        # Set window icon
        try:
            self.root.iconphoto(True, self.window_icon)
        except Exception as e:
            print(f"Could not set window icon: {e}")
        
        # Store PIL image for tray icon
        self.icon_image = image
        
        return image

    def setup_window(self):
        """Configure main window"""
        self.root.title("Professional Time Calculator")
        self.root.geometry("950x700")
        self.root.configure(bg='#f5f5f5')
        self.root.minsize(800, 600)
        
        # Handle window close event
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def setup_styles(self):
        """Configure professional styling"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

    def create_interface(self):
        """Create the main user interface"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Header
        self.create_header(main_frame)

        # Input section
        self.create_input_section(main_frame)

        # Buttons
        self.create_buttons(main_frame)

        # Results section
        self.create_results_section(main_frame)

        # Status bar
        self.create_status_bar(main_frame)

    def create_header(self, parent):
        """Create header section"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(
            header_frame,
            text="Professional Time Calculator",
            font=('Arial', 18, 'bold')
        )
        title_label.pack(anchor='w')

        subtitle_label = ttk.Label(
            header_frame,
            text="Advanced time arithmetic with scalar multiplication • Press Enter to calculate",
            font=('Arial', 10)
        )
        subtitle_label.pack(anchor='w', pady=(5, 0))

    def create_input_section(self, parent):
        """Create input section"""
        input_frame = ttk.LabelFrame(parent, text="Time Calculation Input", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 15))

        input_label = ttk.Label(input_frame, text="Enter your calculation:")
        input_label.pack(anchor='w', pady=(0, 5))

        self.input_text = tk.Text(
            input_frame,
            height=4,
            font=('Consolas', 11),
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.X, pady=(0, 10))

        examples_text = """Examples:
• now + 30m                    • 2:56am + 3.5h                • 2025-08-19 17:00:15 + 17m
• 14:30 - 1h 15m              • 2025/12/25 - now             • 12:00pm + 2w 3d 4.5h
• 23:59:59.5 + 1s             • 1y 6mo 2w 3d 4h 5m 6s         • 2025/01/01 09:00 - 2024/12/31 17:30
• 3 * 2h 30m                  • 2.5 * 1h 20m                 • now + 1.5 * 45m"""

        examples_label = ttk.Label(
            input_frame,
            text=examples_text,
            font=('Arial', 9),
            foreground='#666666'
        )
        examples_label.pack(anchor='w')

    def create_buttons(self, parent):
        """Create button section"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        ttk.Button(
            button_frame,
            text="Calculate",
            command=self.calculate,
            style='Accent.TButton'
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Clear",
            command=self.clear_input
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Insert 'now'",
            command=self.insert_now
        ).pack(side=tk.LEFT, padx=(0, 10))

        ttk.Button(
            button_frame,
            text="Help (F1)",
            command=self.show_help
        ).pack(side=tk.LEFT)

    def create_results_section(self, parent):
        """Create results section"""
        results_frame = ttk.LabelFrame(parent, text="Results", padding="15")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Text widget with scrollbar
        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        self.results_text = tk.Text(
            text_frame,
            font=('Consolas', 10),
            wrap=tk.WORD,
            state=tk.DISABLED,
            bg='white'
        )

        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        # Welcome message
        self.display_welcome()

    def create_status_bar(self, parent):
        """Create status bar"""
        self.status_var = tk.StringVar(value="Ready • Enter calculation and press Enter")
        status_label = ttk.Label(
            parent,
            textvariable=self.status_var,
            relief=tk.SUNKEN,
            anchor=tk.W,
            padding=(5, 3)
        )
        status_label.pack(fill=tk.X, side=tk.BOTTOM)

    def bind_shortcuts(self):
        """Bind keyboard shortcuts"""
        self.root.bind('<Return>', lambda e: self.calculate())
        self.root.bind('<Control-Return>', lambda e: self.calculate())
        self.input_text.bind('<Return>', lambda e: self.calculate())
        self.root.bind('<F1>', lambda e: self.show_help())
        self.root.bind('<Control-l>', lambda e: self.clear_input())
        self.root.bind('<Control-h>', lambda e: self.toggle_window())  # Hide/show shortcut

    def setup_tray(self):
        """Setup system tray icon if available"""
        if not TRAY_AVAILABLE:
            return
            
        try:
            # Create tray menu
            menu = pystray.Menu(
                item('Open Calculator', self.show_window),
                item('Quick Calculate', self.quick_calculate),
                pystray.Menu.SEPARATOR,
                item('Current Time', self.show_current_time),
                item('Help', self.show_help),
                pystray.Menu.SEPARATOR,
                item('Exit', self.quit_application)
            )
            
            # Create tray icon
            self.tray_icon = pystray.Icon(
                "time_calculator",
                self.icon_image,
                "Time Calculator",
                menu
            )
            
            # Start tray icon in separate thread
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            
        except Exception as e:
            print(f"Could not setup system tray: {e}")
            self.tray_icon = None

    def on_closing(self):
        """Handle window close event"""
        if TRAY_AVAILABLE and self.tray_icon:
            # Minimize to tray instead of closing
            self.hide_window()
        else:
            # No tray support, close normally
            self.quit_application()

    def hide_window(self):
        """Hide window to system tray"""
        self.root.withdraw()
        self.is_hidden = True

    def show_window(self):
        """Show window from system tray"""
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_hidden = False

    def toggle_window(self):
        """Toggle window visibility"""
        if self.is_hidden:
            self.show_window()
        else:
            self.hide_window()

    def quick_calculate(self):
        """Quick calculation dialog from tray"""
        if not TRAY_AVAILABLE:
            return
            
        # Create a simple input dialog
        dialog = tk.Toplevel()
        dialog.title("Quick Time Calculation")
        dialog.geometry("400x150")
        dialog.resizable(False, False)
        
        # Center the dialog
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Input field
        tk.Label(dialog, text="Enter calculation:", font=('Arial', 10)).pack(pady=10)
        
        entry = tk.Entry(dialog, font=('Consolas', 11), width=40)
        entry.pack(pady=5)
        entry.focus_set()
        
        # Result label
        result_label = tk.Label(dialog, text="", font=('Arial', 9), wraplength=350)
        result_label.pack(pady=10)
        
        def calculate_quick():
            try:
                expression = entry.get().strip()
                if not expression:
                    return
                    
                result = self.parse_and_calculate(expression)
                
                if isinstance(result, timedelta):
                    total_seconds = result.total_seconds()
                    days = int(total_seconds // 86400)
                    hours = int((total_seconds % 86400) // 3600)
                    minutes = int((total_seconds % 3600) // 60)
                    seconds = total_seconds % 60
                    result_text = f"Duration: {days}d {hours}h {minutes}m {seconds:.1f}s"
                else:
                    result_text = f"Result: {result.strftime('%Y-%m-%d %H:%M:%S')}"
                    
                result_label.config(text=result_text)
                
            except Exception as e:
                result_label.config(text=f"Error: {str(e)}")
        
        # Buttons
        button_frame = tk.Frame(dialog)
        button_frame.pack(pady=10)
        
        tk.Button(button_frame, text="Calculate", command=calculate_quick).pack(side=tk.LEFT, padx=5)
        tk.Button(button_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        # Bind Enter key
        entry.bind('<Return>', lambda e: calculate_quick())

    def show_current_time(self):
        """Show current time notification"""
        if not TRAY_AVAILABLE:
            return
            
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self.tray_icon.notify(
                "Current Time",
                current_time,
                timeout=3
            )
        except Exception as e:
            print(f"Could not show notification: {e}")

    def quit_application(self):
        """Properly quit the application"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()

    def insert_now(self):
        """Insert current timestamp"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.input_text.insert(tk.INSERT, now)
        self.input_text.focus_set()

    def clear_input(self):
        """Clear input field"""
        self.input_text.delete('1.0', tk.END)
        self.input_text.focus_set()

    def calculate(self):
        """Main calculation function"""
        try:
            expression = self.input_text.get('1.0', tk.END).strip()
            if not expression:
                self.status_var.set("Please enter a calculation")
                return

            self.status_var.set("Calculating...")
            self.root.update()

            result = self.parse_and_calculate(expression)
            self.display_results(expression, result)
            self.status_var.set("Calculation completed successfully")

        except Exception as e:
            error_msg = f"Error: {str(e)}"
            self.status_var.set(error_msg)
            messagebox.showerror(
                "Calculation Error",
                f"Unable to process calculation:\n\n{str(e)}\n\nPlease check your input format."
            )

    def parse_and_calculate(self, expression):
        """Parse and calculate time expressions"""
        # Clean expression
        expression = expression.replace('\n', ' ').replace('\r', '').strip()

        # Handle 'now' keyword
        if 'now' in expression.lower():
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expression = re.sub(r'\bnow\b', now_str, expression, flags=re.IGNORECASE)

        # Tokenize the expression
        tokens = self.smart_tokenize(expression)

        if len(tokens) < 3:
            raise ValueError("Expression must contain at least one operator (+, -, or *)")

        # Parse first token - could be datetime, duration, or number
        first_token = tokens[0]
        if self.is_number(first_token) and len(tokens) >= 3 and tokens[1] == '*':
            # This is number * duration pattern
            base_time = float(first_token)
        else:
            # Regular datetime/duration
            base_time = self.parse_datetime_or_duration(first_token)
            if not isinstance(base_time, datetime):
                raise ValueError("First value must be a valid date/time (or use number * duration)")

        result_time = base_time

        # Process operations
        i = 1
        while i < len(tokens):
            if i + 1 >= len(tokens):
                break

            operator = tokens[i]
            operand_str = tokens[i + 1]

            if operator == '+':
                operand = self.parse_datetime_or_duration(operand_str)
                if isinstance(operand, (int, float)):
                    raise ValueError("Cannot add a number directly. Use: datetime + duration or number * duration")
                elif isinstance(operand, datetime):
                    # Adding datetime - treat as duration from base epoch
                    if operand.date() == datetime(1900, 1, 1).date():
                        duration = timedelta(
                            hours=operand.hour,
                            minutes=operand.minute,
                            seconds=operand.second,
                            microseconds=operand.microsecond
                        )
                        result_time += duration
                    else:
                        duration = operand - datetime(1900, 1, 1)
                        result_time += duration
                else:
                    # operand is timedelta
                    if isinstance(result_time, (int, float)):
                        raise ValueError("Cannot add duration to number. Use: number * duration + datetime")
                    result_time += operand

            elif operator == '-':
                operand = self.parse_datetime_or_duration(operand_str)
                if isinstance(operand, (int, float)):
                    raise ValueError("Cannot subtract a number directly. Use: datetime - duration")
                elif isinstance(operand, datetime):
                    return result_time - operand
                else:
                    # operand is timedelta
                    if isinstance(result_time, (int, float)):
                        raise ValueError("Cannot subtract duration from number")
                    result_time -= operand

            elif operator == '*':
                # Handle multiplication: number * duration
                if isinstance(result_time, datetime):
                    raise ValueError("Cannot multiply a datetime. Use: number * duration")
                
                operand = self.parse_datetime_or_duration(operand_str)
                if isinstance(operand, datetime):
                    raise ValueError("Cannot multiply by a datetime. Use: number * duration")
                elif isinstance(operand, (int, float)):
                    raise ValueError("Cannot multiply number * number. Use: number * duration")
                
                # result_time is number, operand is timedelta
                result_time = result_time * operand

            i += 2

        return result_time

    def smart_tokenize(self, expression):
        """Smart tokenization that handles dates and multiplication properly"""
        tokens = []
        current_token = ""
        i = 0

        while i < len(expression):
            char = expression[i]

            if char in '+-*':
                if self.is_operator_at_position(expression, i, current_token, char):
                    # This is an operator
                    if current_token.strip():
                        tokens.append(current_token.strip())
                    tokens.append(char)
                    current_token = ""
                else:
                    # This is part of content (like date)
                    current_token += char
            else:
                current_token += char
            i += 1

        # Add final token
        if current_token.strip():
            tokens.append(current_token.strip())

        return tokens

    def is_operator_at_position(self, expression, pos, current_token, char=''):
        """Determine if +/-/* at position is an operator"""
        if not current_token.strip():
            return False

        operator_char = char or expression[pos]
        after = expression[pos + 1:].lstrip() if pos < len(expression) - 1 else ""

        # Multiplication is always an operator when surrounded by space or between tokens
        if operator_char == '*':
            return True

        # Check for date patterns - don't split dates  
        if operator_char == '-':
            # Check if we're in middle of YYYY-MM-DD
            if re.search(r'\d{4}$', current_token) and re.match(r'^\d{2}', after):
                return False
            if re.search(r'\d{4}-\d{2}$', current_token) and re.match(r'^\d{2}', after):
                return False

        # If current token looks like complete datetime and after looks like duration/number
        if self.is_complete_datetime(current_token.strip()):
            if self.is_duration_start(after) or self.is_number_start(after):
                return True

        # If current token is a number and after looks like duration, * is operator
        if operator_char == '*' and self.is_number(current_token.strip()) and self.is_duration_start(after):
            return True

        # Check for whitespace around operator
        has_space_before = pos > 0 and expression[pos - 1].isspace()
        has_space_after = pos < len(expression) - 1 and expression[pos + 1].isspace()

        return has_space_before or has_space_after

    def is_complete_datetime(self, token):
        """Check if token is a complete datetime"""
        patterns = [
            r'^\d{4}-\d{2}-\d{2}(\s+\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(\s*[ap]m)?)?$',
            r'^\d{4}/\d{2}/\d{2}(\s+\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(\s*[ap]m)?)?$',
            r'^\d{1,2}/\d{1,2}/\d{4}(\s+\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(\s*[ap]m)?)?$',
            r'^\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(\s*[ap]m)?$',
        ]
        return any(re.match(pattern, token, re.IGNORECASE) for pattern in patterns)

    def is_duration_start(self, text):
        """Check if text starts with duration pattern"""
        patterns = [
            r'^\d+(\.\d+)?[yY]',
            r'^\d+(\.\d+)?mo',
            r'^\d+(\.\d+)?[wW]',
            r'^\d+(\.\d+)?[dD]',
            r'^\d+(\.\d+)?[hH]',
            r'^\d+(\.\d+)?[mM](?!o)',
            r'^\d+(\.\d+)?[sS]',
        ]
        return any(re.match(pattern, text) for pattern in patterns)

    def is_number_start(self, text):
        """Check if text starts with a number"""
        return re.match(r'^\d+(\.\d+)?', text) is not None

    def is_number(self, text):
        """Check if text is a number"""
        try:
            float(text)
            return True
        except ValueError:
            return False

    def parse_datetime_or_duration(self, text):
        """Parse text as datetime, duration, or number"""
        text = text.strip()

        # Check if it's a number first (for multiplication)
        if self.is_number(text):
            return float(text)

        # Check if it's datetime format
        if self.is_datetime_format(text):
            return self.parse_datetime(text)
        else:
            return self.parse_duration(text)

    def is_datetime_format(self, text):
        """Check if text is datetime format"""
        patterns = [
            r'\d{1,2}:\d{2}',
            r'\d{4}[-/]\d{2}[-/]\d{2}',
            r'\d{1,2}/\d{1,2}/\d{4}',
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def parse_datetime(self, time_str):
        """Parse datetime string"""
        time_str = time_str.strip()

        formats = [
            "%Y-%m-%d %H:%M:%S.%f",
            "%Y-%m-%d %H:%M:%S",
            "%Y-%m-%d %H:%M",
            "%Y-%m-%d %I:%M:%S %p",
            "%Y-%m-%d %I:%M %p",
            "%Y/%m/%d %H:%M:%S.%f",
            "%Y/%m/%d %H:%M:%S",
            "%Y/%m/%d %H:%M",
            "%Y/%m/%d %I:%M:%S %p",
            "%Y/%m/%d %I:%M %p",
            "%m/%d/%Y %H:%M:%S",
            "%m/%d/%Y %H:%M",
            "%m/%d/%Y %I:%M %p",
            "%H:%M:%S.%f",
            "%H:%M:%S",
            "%H:%M",
            "%I:%M:%S %p",
            "%I:%M %p",
            "%Y-%m-%d",
            "%Y/%m/%d",
            "%m/%d/%Y",
        ]

        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue

        # Handle decimal seconds
        decimal_match = re.match(
            r'^(\d{1,2}):(\d{2}):(\d{1,2}(?:\.\d+)?)(?:\s*(am|pm))?$',
            time_str,
            re.IGNORECASE
        )
        if decimal_match:
            hours = int(decimal_match.group(1))
            minutes = int(decimal_match.group(2))
            seconds_float = float(decimal_match.group(3))
            ampm = decimal_match.group(4)

            if minutes >= 60 or seconds_float >= 60:
                raise ValueError(f"Invalid time values: {minutes}m {seconds_float}s")

            if ampm:
                if hours < 1 or hours > 12:
                    raise ValueError(f"Invalid 12-hour format: {hours}")
                if ampm.lower() == 'pm' and hours != 12:
                    hours += 12
                elif ampm.lower() == 'am' and hours == 12:
                    hours = 0
            else:
                if hours >= 24:
                    raise ValueError(f"Invalid 24-hour format: {hours}")

            seconds = int(seconds_float)
            microseconds = int((seconds_float - seconds) * 1000000)
            return datetime(1900, 1, 1, hours, minutes, seconds, microseconds)

        raise ValueError(f"Unable to parse datetime: {time_str}")

    def parse_duration(self, duration_str):
        """Parse duration string"""
        duration_str = duration_str.strip().lower()

        # Simple decimal hours
        if re.match(r'^\d+(\.\d+)?h$', duration_str):
            hours = float(duration_str[:-1])
            return timedelta(hours=hours)

        total_delta = timedelta()

        patterns = {
            r'(\d+(?:\.\d+)?)y': 'years',
            r'(\d+(?:\.\d+)?)mo': 'months',
            r'(\d+(?:\.\d+)?)w': 'weeks',
            r'(\d+(?:\.\d+)?)d': 'days',
            r'(\d+(?:\.\d+)?)h': 'hours',
            r'(\d+(?:\.\d+)?)m(?!o)': 'minutes',
            r'(\d+(?:\.\d+)?)s': 'seconds'
        }

        for pattern, unit in patterns.items():
            matches = re.findall(pattern, duration_str)
            for match in matches:
                value = float(match)

                if unit == 'years':
                    total_delta += timedelta(days=value * 365.25)
                elif unit == 'months':
                    total_delta += timedelta(days=value * 30.44)
                elif unit == 'weeks':
                    total_delta += timedelta(weeks=value)
                elif unit == 'days':
                    total_delta += timedelta(days=value)
                elif unit == 'hours':
                    total_delta += timedelta(hours=value)
                elif unit == 'minutes':
                    total_delta += timedelta(minutes=value)
                elif unit == 'seconds':
                    total_delta += timedelta(seconds=value)

        if total_delta == timedelta():
            raise ValueError(f"Unable to parse duration: {duration_str}")

        return total_delta

    def display_welcome(self):
        """Display welcome message"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)

        welcome = """🕐 Professional Time Calculator

Welcome! This calculator supports:

✓ Multiple date/time formats (YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY)
✓ Time formats (24h, 12h AM/PM, decimal seconds)  
✓ Duration units (years, months, weeks, days, hours, minutes, seconds)
✓ Decimal precision (3.5h, 2.25d, 45.5s)
✓ Current time with 'now' keyword
✓ Duration multiplication (3 * 2h 30m)

Enter a calculation above and press Enter!

Quick examples:
• now + 30m
• 2025-12-25 - now
• 14:30:45.5 + 2h 15m
• 3 * 1h 30m"""

        self.results_text.insert(tk.END, welcome)
        self.results_text.config(state=tk.DISABLED)

    def display_results(self, expression, result):
        """Display calculation results"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)

        # Header
        self.results_text.insert(tk.END, "=" * 70 + "\n")
        self.results_text.insert(tk.END, f"CALCULATION: {expression}\n")
        self.results_text.insert(tk.END, "=" * 70 + "\n\n")

        if isinstance(result, timedelta):
            self.display_duration_result(result)
        else:
            self.display_datetime_result(result)

        self.results_text.insert(tk.END, "\n" + "=" * 70 + "\n")
        self.results_text.config(state=tk.DISABLED)
        self.results_text.see('1.0')

    def display_duration_result(self, duration):
        """Display duration results"""
        self.results_text.insert(tk.END, "⏱️  DURATION RESULT\n")
        self.results_text.insert(tk.END, "-" * 40 + "\n\n")

        total_seconds = duration.total_seconds()
        abs_seconds = abs(total_seconds)

        days = int(abs_seconds // 86400)
        hours = int((abs_seconds % 86400) // 3600)
        minutes = int((abs_seconds % 3600) // 60)
        seconds = abs_seconds % 60

        sign = "-" if total_seconds < 0 else ""

        self.results_text.insert(tk.END, f"Duration: {sign}{days}d {hours}h {minutes}m {seconds:.3f}s\n\n")

        conversions = [
            ("Total Seconds", f"{total_seconds:.3f}"),
            ("Total Minutes", f"{total_seconds/60:.3f}"),
            ("Total Hours", f"{total_seconds/3600:.3f}"),
            ("Total Days", f"{total_seconds/86400:.3f}"),
            ("Total Weeks", f"{total_seconds/(86400*7):.3f}"),
        ]

        for label, value in conversions:
            self.results_text.insert(tk.END, f"{label:14}: {value}\n")

    def display_datetime_result(self, dt):
        """Display datetime results"""
        self.results_text.insert(tk.END, "📅 DATE/TIME RESULT\n")
        self.results_text.insert(tk.END, "-" * 40 + "\n\n")

        formats = [
            ("Standard", dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]),
            ("ISO Format", dt.isoformat()),
            ("12-Hour", dt.strftime("%Y-%m-%d %I:%M:%S %p")),
            ("US Format", dt.strftime("%m/%d/%Y %I:%M:%S %p")),
            ("Date Only", dt.strftime("%Y-%m-%d")),
            ("Time Only", dt.strftime("%H:%M:%S.%f")[:-3]),
            ("Weekday", dt.strftime("%A, %B %d, %Y")),
            ("Timestamp", str(int(dt.timestamp()))),
        ]

        for label, formatted in formats:
            self.results_text.insert(tk.END, f"{label:12}: {formatted}\n")

        self.results_text.insert(tk.END, f"\n📊 CALENDAR INFO\n")
        self.results_text.insert(tk.END, "-" * 25 + "\n")

        calendar_info = [
            ("Day of Year", str(dt.timetuple().tm_yday)),
            ("Week Number", str(dt.isocalendar()[1])),
            ("Quarter", f"Q{(dt.month-1)//3 + 1}"),
        ]

        for label, value in calendar_info:
            self.results_text.insert(tk.END, f"{label:12}: {value}\n")

    def show_help(self):
        """Show help dialog"""
        help_text = """📖 PROFESSIONAL TIME CALCULATOR - HELP

🕐 TIME FORMATS:
• 24-hour: 14:30, 14:30:45, 14:30:45.5
• 12-hour: 2:30pm, 2:30:45pm, 2:30:45.5am
• Current: now

📅 DATE FORMATS:
• ISO: 2025-08-19, 2025-08-19 14:30:45
• US: 08/19/2025, 08/19/2025 2:30pm
• International: 2025/08/19, 2025/08/19 16:51:00

⏱️ DURATION UNITS:
• y = years (365.25 days)
• mo = months (30.44 days)
• w = weeks, d = days, h = hours
• m = minutes, s = seconds

🧮 EXAMPLES:
• now + 30m
• 2025-12-25 - now
• 14:30 + 2h 15m 30s
• 2025/08/19 16:51:00 + 1y 2mo

✖️ MULTIPLICATION:
• 3 * 2h 30m (multiply duration by scalar)
• 2.5 * 1h 20m
• now + 1.5 * 45m
• 0.5 * 4d 6h

⌨️ SHORTCUTS:
• Enter: Calculate
• Ctrl+L: Clear
• F1: Help"""

        messagebox.showinfo("Help", help_text)


def main():
    """Main application entry point"""
    root = tk.Tk()
    app = TimeCalculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
