#!/usr/bin/env python3
"""
Advanced Time Calculator for Linux
A comprehensive GUI application for time calculations with date support, scalar multiplication,
flexible operations, and progress estimation with compound time specifiers
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime, timedelta
import threading
import math

# Import dependencies with fallbacks
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False

try:
    from PIL import ImageTk
    IMAGETK_AVAILABLE = True
except ImportError:
    IMAGETK_AVAILABLE = False

try:
    import pystray
    from pystray import MenuItem as item
    TRAY_AVAILABLE = True and PIL_AVAILABLE
except ImportError:
    TRAY_AVAILABLE = False


class AdvancedTimeCalculator:
    def __init__(self, root):
        self.root = root
        self.tray_icon = None
        self.is_hidden = False
        
        # Initialize components
        self.setup_window()
        self.create_icon()
        self.setup_styles()
        self.create_interface()
        self.bind_shortcuts()
        self.setup_tray()

    def setup_window(self):
        """Configure main window properties"""
        self.root.title("Advanced Time Calculator")
        self.root.geometry("980x720")
        self.root.configure(bg='#f5f5f5')
        self.root.minsize(800, 600)
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)

    def create_icon(self):
        """Create custom application icon"""
        if not PIL_AVAILABLE:
            self.root.title("🕐 Advanced Time Calculator")
            self.icon_image = None
            return None
            
        try:
            # Create 64x64 icon
            size = 64
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Draw clock face
            margin = 4
            circle_bbox = [margin, margin, size-margin, size-margin]
            draw.ellipse(circle_bbox, fill='#2c3e50', outline='#34495e', width=2)
            
            center = size // 2
            
            # Draw clock hands
            hour_end_x = center + 12
            hour_end_y = center
            draw.line([center, center, hour_end_x, hour_end_y], fill='white', width=4)
            
            minute_end_x = center
            minute_end_y = center - 16
            draw.line([center, center, minute_end_x, minute_end_y], fill='white', width=3)
            
            # Draw hour markers
            for hour in range(12):
                angle = hour * 30
                angle_rad = math.radians(angle - 90)
                
                outer_x = center + 20 * math.cos(angle_rad)
                outer_y = center + 20 * math.sin(angle_rad)
                inner_x = center + 16 * math.cos(angle_rad)
                inner_y = center + 16 * math.sin(angle_rad)
                
                draw.line([inner_x, inner_y, outer_x, outer_y], fill='white', width=2)
            
            # Center dot
            dot_size = 3
            draw.ellipse([center-dot_size, center-dot_size, center+dot_size, center+dot_size], 
                        fill='white')
            
            # Calculator symbol in corner
            calc_size = 12
            calc_x = size - calc_size - 4
            calc_y = size - calc_size - 4
            draw.rectangle([calc_x, calc_y, calc_x + calc_size, calc_y + calc_size], 
                          fill='#3498db', outline='#2980b9')
            
            # Plus symbol on calculator
            plus_x = calc_x + calc_size // 2
            plus_y = calc_y + calc_size // 2
            draw.line([plus_x - 3, plus_y, plus_x + 3, plus_y], fill='white', width=2)
            draw.line([plus_x, plus_y - 3, plus_x, plus_y + 3], fill='white', width=2)
            
            # Set window icon if possible
            if IMAGETK_AVAILABLE:
                self.window_icon = ImageTk.PhotoImage(image)
                self.root.iconphoto(True, self.window_icon)
            
            self.icon_image = image
            return image
            
        except Exception as e:
            print(f"Error creating icon: {e}")
            self.root.title("🕐 Advanced Time Calculator")
            self.icon_image = None
            return None

    def setup_styles(self):
        """Configure TTK styling"""
        self.style = ttk.Style()
        self.style.theme_use('clam')

    def create_interface(self):
        """Create the main user interface"""
        main_frame = ttk.Frame(self.root, padding="20")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create sections
        self.create_header(main_frame)
        self.create_input_section(main_frame)
        self.create_buttons(main_frame)
        self.create_results_section(main_frame)
        self.create_status_bar(main_frame)

    def create_header(self, parent):
        """Create application header"""
        header_frame = ttk.Frame(parent)
        header_frame.pack(fill=tk.X, pady=(0, 20))

        title_label = ttk.Label(
            header_frame,
            text="Advanced Time Calculator",
            font=('Arial', 18, 'bold')
        )
        title_label.pack(anchor='w')

        subtitle_label = ttk.Label(
            header_frame,
            text="Time arithmetic with progress estimation and flexible operations • Press Enter to calculate",
            font=('Arial', 10)
        )
        subtitle_label.pack(anchor='w', pady=(5, 0))

    def create_input_section(self, parent):
        """Create input section with examples"""
        input_frame = ttk.LabelFrame(parent, text="Time Calculation Input", padding="15")
        input_frame.pack(fill=tk.X, pady=(0, 15))

        # Input label
        input_label = ttk.Label(input_frame, text="Enter your calculation:")
        input_label.pack(anchor='w', pady=(0, 5))

        # Input text area
        self.input_text = tk.Text(
            input_frame,
            height=4,
            font=('Consolas', 11),
            wrap=tk.WORD
        )
        self.input_text.pack(fill=tk.X, pady=(0, 10))

        # Examples
        examples_text = """Examples:
• now + 30m                     • 2:56am + 3.5h                 • 2025-08-19 17:00:15 + 17m
• 14:30 - 1h 15m               • 2025/12/25 - now              • 12:00pm + 2w 3d 4.5h
• 3d + now                     • 45m * 2 + now                 • 3 * 2h 30m
• 1d45m15s@20% (total time)    • progress(2h30m, 50%, remaining) • 20% in 1h30m45s"""

        examples_label = ttk.Label(
            input_frame,
            text=examples_text,
            font=('Arial', 9),
            foreground='#666666'
        )
        examples_label.pack(anchor='w')

    def create_buttons(self, parent):
        """Create action buttons"""
        button_frame = ttk.Frame(parent)
        button_frame.pack(fill=tk.X, pady=(0, 15))

        # Main buttons
        ttk.Button(button_frame, text="Calculate", command=self.calculate).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Clear", command=self.clear_input).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Insert 'now'", command=self.insert_now).pack(side=tk.LEFT, padx=(0, 10))
        ttk.Button(button_frame, text="Help (F1)", command=self.show_help).pack(side=tk.LEFT, padx=(0, 10))
        
        # Tray button if available
        if TRAY_AVAILABLE:
            ttk.Button(button_frame, text="Minimize to Tray", command=self.hide_window).pack(side=tk.LEFT)

    def create_results_section(self, parent):
        """Create results display area"""
        results_frame = ttk.LabelFrame(parent, text="Results", padding="15")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 10))

        # Text area with scrollbar
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

        # Show welcome message
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
        self.root.bind('<Control-h>', lambda e: self.toggle_window())

    def setup_tray(self):
        """Setup system tray integration"""
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
                "Advanced Time Calculator",
                menu
            )
            
            # Start in background thread
            self.tray_thread = threading.Thread(target=self.tray_icon.run, daemon=True)
            self.tray_thread.start()
            
        except Exception as e:
            print(f"Could not setup system tray: {e}")
            self.tray_icon = None

    # Window management methods
    def on_closing(self):
        """Handle window close event"""
        if TRAY_AVAILABLE and self.tray_icon:
            self.hide_window()
        else:
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

    def quit_application(self):
        """Properly quit the application"""
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()

    # Tray-specific methods
    def quick_calculate(self):
        """Quick calculation dialog from system tray"""
        if not TRAY_AVAILABLE:
            return
            
        dialog = tk.Toplevel()
        dialog.title("Quick Time Calculation")
        dialog.geometry("420x160")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        # Input
        tk.Label(dialog, text="Enter calculation:", font=('Arial', 10)).pack(pady=10)
        
        entry = tk.Entry(dialog, font=('Consolas', 11), width=45)
        entry.pack(pady=5)
        entry.focus_set()
        
        # Result display
        result_label = tk.Label(dialog, text="", font=('Arial', 9), wraplength=380)
        result_label.pack(pady=10)
        
        def calculate_quick():
            try:
                expression = entry.get().strip()
                if not expression:
                    return
                    
                result = self.parse_and_calculate(expression)
                
                if isinstance(result, timedelta):
                    result_text = self.format_duration_friendly(result)
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
        
        # Enter key binding
        entry.bind('<Return>', lambda e: calculate_quick())

    def show_current_time(self):
        """Show current time notification via tray"""
        if not TRAY_AVAILABLE:
            return
            
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        
        try:
            self.tray_icon.notify("Current Time", current_time, timeout=3)
        except Exception as e:
            print(f"Could not show notification: {e}")

    # Input handling methods
    def insert_now(self):
        """Insert current timestamp at cursor"""
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.input_text.insert(tk.INSERT, now)
        self.input_text.focus_set()

    def clear_input(self):
        """Clear input field and focus"""
        self.input_text.delete('1.0', tk.END)
        self.input_text.focus_set()

    def calculate(self):
        """Main calculation entry point"""
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

    # Core calculation logic
    def parse_and_calculate(self, expression):
        """Main parsing and calculation engine"""
        # Clean the expression
        expression = expression.replace('\n', ' ').replace('\r', '').strip()

        # Handle 'now' keyword replacement
        if 'now' in expression.lower():
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expression = re.sub(r'\bnow\b', now_str, expression, flags=re.IGNORECASE)

        # Convert progress syntax to function calls
        expression = self.handle_progress_syntax(expression)

        # Handle progress functions directly (before tokenization)
        if expression.lower().startswith('progress('):
            return self.calculate_progress(expression)

        # Check for progress function that might have gotten through
        if 'progress(' in expression.lower() and expression.count('(') == 1 and expression.count(')') == 1:
            return self.calculate_progress(expression)

        # Tokenize for complex expressions
        tokens = self.smart_tokenize(expression)

        # Handle single progress function token
        if len(tokens) == 1 and 'progress(' in tokens[0].lower():
            return self.calculate_progress(tokens[0])

        if len(tokens) < 3:
            raise ValueError("Expression must contain at least one operator (+, -, or *)")

        # Parse the first token
        first_token = tokens[0]
        
        # Determine the type of calculation
        if self.is_number(first_token) and len(tokens) >= 3 and tokens[1] == '*':
            # Pattern: number * duration
            base_time = float(first_token)
        else:
            # Handle duration + datetime patterns (e.g., "3d + now")
            parsed_first = self.parse_datetime_or_duration(first_token)
            
            if isinstance(parsed_first, timedelta) and len(tokens) >= 3 and tokens[1] == '+':
                second_operand = self.parse_datetime_or_duration(tokens[2])
                if isinstance(second_operand, datetime):
                    return second_operand + parsed_first
            
            base_time = parsed_first

        result_time = base_time

        # Process operations sequentially
        i = 1
        while i < len(tokens):
            if i + 1 >= len(tokens):
                break

            operator = tokens[i]
            operand_str = tokens[i + 1]

            if operator == '+':
                operand = self.parse_datetime_or_duration(operand_str)
                
                if isinstance(operand, (int, float)):
                    raise ValueError("Cannot add a number directly. Use duration or datetime.")
                elif isinstance(operand, datetime):
                    if isinstance(result_time, timedelta):
                        result_time = operand + result_time
                    elif isinstance(result_time, datetime):
                        # Handle time-only additions
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
                        raise ValueError("Invalid addition operation")
                else:
                    # Adding timedelta
                    if isinstance(result_time, (int, float)):
                        raise ValueError("Cannot add duration to number")
                    elif isinstance(result_time, datetime):
                        result_time += operand
                    elif isinstance(result_time, timedelta):
                        result_time += operand

            elif operator == '-':
                operand = self.parse_datetime_or_duration(operand_str)
                if isinstance(operand, (int, float)):
                    raise ValueError("Cannot subtract a number directly")
                elif isinstance(operand, datetime):
                    return result_time - operand
                else:
                    if isinstance(result_time, (int, float)):
                        raise ValueError("Cannot subtract duration from number")
                    result_time -= operand

            elif operator == '*':
                if isinstance(result_time, datetime):
                    raise ValueError("Cannot multiply a datetime. Use: number * duration")
                
                operand = self.parse_datetime_or_duration(operand_str)
                if isinstance(operand, datetime):
                    raise ValueError("Cannot multiply by a datetime")
                elif isinstance(operand, (int, float)):
                    raise ValueError("Cannot multiply number * number. Use: number * duration")
                
                # Multiply number by duration
                result_time = result_time * operand

            i += 2

        return result_time

    def handle_progress_syntax(self, expression):
        """Convert various progress syntaxes to function calls"""
        # Convert @ syntax: "1h15s@15%" -> "progress(1h15s, 15%)"
        # This pattern handles compound durations like 1h15s, 1d45m15s, etc.
        at_pattern = r'([0-9]+(?:\.[0-9]+)?[a-zA-Z]+(?:[0-9]+(?:\.[0-9]+)?[a-zA-Z]+)*)\s*@\s*([0-9]+(?:\.[0-9]+)?)%'
        expression = re.sub(at_pattern, r'progress(\1, \2%)', expression, flags=re.IGNORECASE)
        
        # Convert percentage-in syntax: "15% in 1h15s" -> "progress(1h15s, 15%)"
        percent_in_pattern = r'([0-9]+(?:\.[0-9]+)?)%\s+in\s+([0-9]+(?:\.[0-9]+)?[a-zA-Z]+(?:[0-9]+(?:\.[0-9]+)?[a-zA-Z]+)*)'
        expression = re.sub(percent_in_pattern, r'progress(\2, \1%)', expression, flags=re.IGNORECASE)
        
        return expression

    def calculate_progress(self, progress_expr):
        """Calculate progress-based time estimates"""
        # Parse progress function: progress(duration, percentage[, mode])
        pattern = r'progress\s*\(\s*([^,]+)\s*,\s*(\d+(?:\.\d+)?)%(?:\s*,\s*(\w+))?\s*\)'
        match = re.match(pattern, progress_expr, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid progress syntax. Use: progress(duration, percentage) or duration@percentage")
        
        duration_str = match.group(1).strip()
        percentage = float(match.group(2))
        mode = match.group(3).lower() if match.group(3) else 'total'
        
        # Validate percentage
        if percentage <= 0 or percentage >= 100:
            raise ValueError("Percentage must be between 0 and 100 (exclusive)")
        
        # Parse elapsed time (supports compound durations like 1d45m15s)
        elapsed_duration = self.parse_duration(duration_str)
        elapsed_seconds = elapsed_duration.total_seconds()
        
        # Calculate total time needed
        total_seconds = elapsed_seconds / (percentage / 100.0)
        total_duration = timedelta(seconds=total_seconds)
        
        # Calculate remaining time
        remaining_seconds = total_seconds - elapsed_seconds
        remaining_duration = timedelta(seconds=remaining_seconds)
        
        # Return based on mode
        if mode == 'total':
            return total_duration
        elif mode == 'remaining':
            return remaining_duration  
        elif mode == 'eta':
            return datetime.now() + remaining_duration
        else:
            raise ValueError(f"Invalid progress mode: {mode}. Use 'total', 'remaining', or 'eta'")

    def smart_tokenize(self, expression):
        """Smart tokenization that preserves function calls"""
        # If this is a complete function call, don't tokenize it
        if re.match(r'^\s*\w+\s*\([^)]*\)\s*$', expression):
            return [expression.strip()]
            
        tokens = []
        current_token = ""
        paren_depth = 0
        i = 0

        while i < len(expression):
            char = expression[i]
            
            # Track parentheses to avoid splitting inside function calls
            if char == '(':
                paren_depth += 1
                current_token += char
            elif char == ')':
                paren_depth -= 1
                current_token += char
            elif char in '+-*' and paren_depth == 0:
                # Only treat as operator if not inside parentheses
                if self.is_operator_at_position(expression, i, current_token):
                    if current_token.strip():
                        tokens.append(current_token.strip())
                    tokens.append(char)
                    current_token = ""
                else:
                    current_token += char
            else:
                current_token += char
            i += 1

        if current_token.strip():
            tokens.append(current_token.strip())

        return tokens

    def is_operator_at_position(self, expression, pos, current_token):
        """Determine if character at position is an operator"""
        if not current_token.strip():
            return False

        char = expression[pos]
        after = expression[pos + 1:].lstrip() if pos < len(expression) - 1 else ""

        # Multiplication is always an operator when spaced
        if char == '*':
            return True

        # Don't split dates (YYYY-MM-DD)
        if char == '-':
            if re.search(r'\d{4}$', current_token) and re.match(r'^\d{2}', after):
                return False
            if re.search(r'\d{4}-\d{2}$', current_token) and re.match(r'^\d{2}', after):
                return False

        # Check for complete datetime followed by duration/number
        if self.is_complete_datetime(current_token.strip()):
            if self.is_duration_start(after) or self.is_number_start(after):
                return True

        # Check for whitespace around operator
        has_space_before = pos > 0 and expression[pos - 1].isspace()
        has_space_after = pos < len(expression) - 1 and expression[pos + 1].isspace()

        return has_space_before or has_space_after

    def is_complete_datetime(self, token):
        """Check if token represents a complete datetime"""
        patterns = [
            r'^\d{4}-\d{2}-\d{2}(\s+\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(\s*[ap]m)?)?$',
            r'^\d{4}/\d{2}/\d{2}(\s+\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(\s*[ap]m)?)?$',
            r'^\d{1,2}/\d{1,2}/\d{4}(\s+\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(\s*[ap]m)?)?$',
            r'^\d{1,2}:\d{2}(:\d{2}(\.\d+)?)?(\s*[ap]m)?$',
        ]
        return any(re.match(pattern, token, re.IGNORECASE) for pattern in patterns)

    def is_duration_start(self, text):
        """Check if text starts with a duration pattern"""
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
        """Check if text is a valid number"""
        try:
            float(text)
            return True
        except ValueError:
            return False

    # Parsing methods
    def parse_datetime_or_duration(self, text):
        """Parse text as datetime, duration, or number"""
        text = text.strip()

        # Handle 'now' keyword
        if text.lower() == 'now':
            return datetime.now()

        # Check if it's a number (for multiplication)
        if self.is_number(text):
            return float(text)

        # Check datetime vs duration
        if self.is_datetime_format(text):
            return self.parse_datetime(text)
        else:
            return self.parse_duration(text)

    def is_datetime_format(self, text):
        """Check if text appears to be a datetime format"""
        patterns = [
            r'\d{1,2}:\d{2}',  # Time patterns
            r'\d{4}[-/]\d{2}[-/]\d{2}',  # Date patterns
            r'\d{1,2}/\d{1,2}/\d{4}',  # US date format
        ]
        return any(re.search(pattern, text) for pattern in patterns)

    def parse_datetime(self, time_str):
        """Parse various datetime formats"""
        time_str = time_str.strip()

        # Try standard datetime formats
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

        # Handle decimal seconds manually
        decimal_match = re.match(
            r'^(\d{1,2}):(\d{2}):(\d{1,2}(?:\.\d+)?)(?:\s*(am|pm))?',
            time_str,
            re.IGNORECASE
        )
        if decimal_match:
            hours = int(decimal_match.group(1))
            minutes = int(decimal_match.group(2))
            seconds_float = float(decimal_match.group(3))
            ampm = decimal_match.group(4)

            # Validate time components
            if minutes >= 60 or seconds_float >= 60:
                raise ValueError(f"Invalid time values: {minutes}m {seconds_float}s")

            # Handle AM/PM
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

            # Convert to datetime
            seconds = int(seconds_float)
            microseconds = int((seconds_float - seconds) * 1000000)
            return datetime(1900, 1, 1, hours, minutes, seconds, microseconds)

        raise ValueError(f"Unable to parse datetime: {time_str}")

    def parse_duration(self, duration_str):
        """Parse duration strings including compound formats like 1d45m15s"""
        duration_str = duration_str.strip().lower()

        # Handle simple decimal hours (e.g., "3.5h")
        if re.match(r'^\d+(\.\d+)?h', duration_str):
            hours = float(duration_str[:-1])
            return timedelta(hours=hours)

        # Initialize total duration
        total_delta = timedelta()

        # Define patterns for all time units
        patterns = {
            r'(\d+(?:\.\d+)?)y': 'years',
            r'(\d+(?:\.\d+)?)mo': 'months',
            r'(\d+(?:\.\d+)?)w': 'weeks',
            r'(\d+(?:\.\d+)?)d': 'days',
            r'(\d+(?:\.\d+)?)h': 'hours',
            r'(\d+(?:\.\d+)?)m(?!o)': 'minutes',  # m but not mo (months)
            r'(\d+(?:\.\d+)?)s': 'seconds'
        }

        # Process each pattern
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

        # Validate that we found something
        if total_delta == timedelta():
            raise ValueError(f"Unable to parse duration: {duration_str}")

        return total_delta

    # Display methods
    def display_welcome(self):
        """Display welcome message"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)

        welcome = """🕐 Advanced Time Calculator

Welcome! This calculator supports:

✓ Multiple date/time formats (YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY)
✓ Time formats (24h, 12h AM/PM, decimal seconds)  
✓ Duration units (years, months, weeks, days, hours, minutes, seconds)
✓ Decimal precision (3.5h, 2.25d, 45.5s)
✓ Current time with 'now' keyword
✓ Duration multiplication (3 * 2h 30m)
✓ Flexible operations (3d + now, 45m * 2 + now)
✓ Progress estimation with compound durations (1d45m15s@20%)
✓ System tray integration

Enter a calculation above and press Enter!

Quick examples:
• now + 30m
• 2025-12-25 - now  
• 3d + now
• 1d45m15s@20% (find total time if 20% done in 1 day 45min 15sec)
• progress(2h30m45s, 35%, remaining)"""

        self.results_text.insert(tk.END, welcome)
        self.results_text.config(state=tk.DISABLED)

    def display_results(self, expression, result):
        """Display calculation results"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)

        # Header
        self.results_text.insert(tk.END, "=" * 75 + "\n")
        self.results_text.insert(tk.END, f"CALCULATION: {expression}\n")
        self.results_text.insert(tk.END, "=" * 75 + "\n\n")

        # Display based on result type
        if isinstance(result, timedelta):
            self.display_duration_result(result, expression)
        else:
            self.display_datetime_result(result)

        self.results_text.insert(tk.END, "\n" + "=" * 75 + "\n")
        self.results_text.config(state=tk.DISABLED)
        self.results_text.see('1.0')

    def display_duration_result(self, duration, expression=""):
        """Display duration results with progress analysis"""
        self.results_text.insert(tk.END, "⏱️  DURATION RESULT\n")
        self.results_text.insert(tk.END, "-" * 45 + "\n\n")

        # Calculate components
        total_seconds = duration.total_seconds()
        abs_seconds = abs(total_seconds)

        days = int(abs_seconds // 86400)
        hours = int((abs_seconds % 86400) // 3600)
        minutes = int((abs_seconds % 3600) // 60)
        seconds = abs_seconds % 60

        sign = "-" if total_seconds < 0 else ""

        # Display duration
        self.results_text.insert(tk.END, f"Duration: {sign}{days}d {hours}h {minutes}m {seconds:.3f}s\n")
        self.results_text.insert(tk.END, f"Friendly: {self.format_duration_friendly(duration)}\n\n")

        # Progress analysis for progress calculations
        if 'progress(' in expression.lower() or '@' in expression:
            self.results_text.insert(tk.END, "📊 PROGRESS ANALYSIS\n")
            self.results_text.insert(tk.END, "-" * 35 + "\n")
            
            if 'eta' in expression.lower():
                eta_time = datetime.now() + duration
                self.results_text.insert(tk.END, f"Estimated completion: {eta_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.results_text.insert(tk.END, f"Time from now: {self.format_duration_friendly(duration)}\n\n")
            elif 'remaining' in expression.lower():
                self.results_text.insert(tk.END, f"Remaining work time: {self.format_duration_friendly(duration)}\n")
                if total_seconds > 0:
                    completion_time = datetime.now() + duration
                    self.results_text.insert(tk.END, f"Expected completion: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}\n\n")
            else:
                # Total time calculation
                self.results_text.insert(tk.END, f"Total project duration: {self.format_duration_friendly(duration)}\n")
                
                # Extract percentage for context
                percent_match = re.search(r'(\d+(?:\.\d+)?)%', expression)
                if percent_match:
                    percent = float(percent_match.group(1))
                    remaining_pct = 100 - percent
                    remaining_time = duration * (remaining_pct / 100)
                    completion_time = datetime.now() + remaining_time
                    self.results_text.insert(tk.END, f"Remaining ({remaining_pct:.1f}%): {self.format_duration_friendly(remaining_time)}\n")
                    self.results_text.insert(tk.END, f"Expected completion: {completion_time.strftime('%Y-%m-%d %H:%M:%S')}\n")
                self.results_text.insert(tk.END, "\n")

        # Unit conversions
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
        """Display datetime results in multiple formats"""
        self.results_text.insert(tk.END, "📅 DATE/TIME RESULT\n")
        self.results_text.insert(tk.END, "-" * 45 + "\n\n")

        # Multiple format representations
        formats = [
            ("Standard", dt.strftime("%Y-%m-%d %H:%M:%S.%f")[:-3]),
            ("ISO Format", dt.isoformat()),
            ("12-Hour", dt.strftime("%Y-%m-%d %I:%M:%S %p")),
            ("US Format", dt.strftime("%m/%d/%Y %I:%M:%S %p")),
            ("Date Only", dt.strftime("%Y-%m-%d")),
            ("Time Only", dt.strftime("%H:%M:%S.%f")[:-3]),
            ("Weekday", dt.strftime("%A, %B %d, %Y")),
            ("Unix Time", str(int(dt.timestamp()))),
        ]

        for label, formatted in formats:
            self.results_text.insert(tk.END, f"{label:12}: {formatted}\n")

        # Calendar information
        self.results_text.insert(tk.END, f"\n📊 CALENDAR INFO\n")
        self.results_text.insert(tk.END, "-" * 30 + "\n")

        calendar_info = [
            ("Day of Year", str(dt.timetuple().tm_yday)),
            ("Week Number", str(dt.isocalendar()[1])),
            ("Quarter", f"Q{(dt.month-1)//3 + 1}"),
        ]

        for label, value in calendar_info:
            self.results_text.insert(tk.END, f"{label:12}: {value}\n")

    def format_duration_friendly(self, duration):
        """Format duration in a human-friendly way"""
        total_seconds = abs(duration.total_seconds())
        
        days = int(total_seconds // 86400)
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        
        parts = []
        if days > 0:
            parts.append(f"{days} day{'s' if days != 1 else ''}")
        if hours > 0:
            parts.append(f"{hours} hour{'s' if hours != 1 else ''}")
        if minutes > 0:
            parts.append(f"{minutes} minute{'s' if minutes != 1 else ''}")
        if seconds > 0 or not parts:
            if seconds == int(seconds):
                parts.append(f"{int(seconds)} second{'s' if int(seconds) != 1 else ''}")
            else:
                parts.append(f"{seconds:.1f} seconds")
        
        # Format nicely
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return f"{', '.join(parts[:-1])}, and {parts[-1]}"

    def show_help(self):
        """Display comprehensive help dialog"""
        help_text = """📖 ADVANCED TIME CALCULATOR - HELP

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
• Compound: 1d45m15s, 2h30m, 1y2mo3w

🧮 BASIC OPERATIONS:
• now + 30m
• 2025-12-25 - now
• 14:30 + 2h 15m 30s
• 2025/08/19 16:51:00 + 1y 2mo

✖️ MULTIPLICATION:
• 3 * 2h 30m (multiply duration by scalar)
• 2.5 * 1h 20m
• now + 1.5 * 45m
• 0.5 * 4d 6h

🔄 FLEXIBLE OPERATIONS:
• 3d + now (duration + datetime)
• 45m * 2 + now (chain operations)
• 2h + 30m (combine durations)

📊 PROGRESS ESTIMATION:
• 1d45m15s@20% (compound duration, 20% complete)
• progress(2h30m45s, 35%) (explicit function)
• progress(1h30m, 40%, remaining) (time left)
• progress(45m, 25%, eta) (completion time)
• 33% in 2h15m30s (natural language)

⌨️ KEYBOARD SHORTCUTS:
• Enter: Calculate
• Ctrl+L: Clear input
• Ctrl+H: Hide/Show window (tray)
• F1: Show this help

🔔 SYSTEM TRAY FEATURES:
• Right-click tray icon for quick access
• Quick Calculate for simple calculations
• Current Time notifications
• Close window minimizes to tray

💡 PROGRESS EXAMPLES:
If a process is 20% complete after 1 day, 45 minutes, and 15 seconds:
• Total time: 1d45m15s@20%
• Time remaining: progress(1d45m15s, 20%, remaining)
• When it finishes: progress(1d45m15s, 20%, eta)"""

        messagebox.showinfo("Advanced Time Calculator - Help", help_text)


def main():
    """Application entry point with dependency checking"""
    print("🕐 Advanced Time Calculator")
    print("=" * 45)
    
    # Check for optional dependencies
    missing_deps = []
    
    if not PIL_AVAILABLE:
        missing_deps.append("PIL/Pillow")
    elif not IMAGETK_AVAILABLE:
        missing_deps.append("ImageTk")
    
    if not TRAY_AVAILABLE:
        missing_deps.append("pystray")
    
    # Report missing dependencies
    if missing_deps:
        print("⚠️  Optional dependencies missing:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print()
        print("📦 To install all features:")
        print("   pip install pillow pystray")
        print()
        print("🐧 On Ubuntu/Debian, you may also need:")
        print("   sudo apt-get install python3-pil.imagetk")
        print()
        print("🚀 Starting with available features...")
        print()
    else:
        print("✅ All features available!")
        print()
    
    # Launch application
    root = tk.Tk()
    app = AdvancedTimeCalculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()
    
