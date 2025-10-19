#!/usr/bin/env python3
"""
Advanced Time Calculator for Linux
Complete rewrite with robust parsing for compound time specifiers and progress calculations
"""

import tkinter as tk
from tkinter import ttk, messagebox
import re
from datetime import datetime, timedelta
import threading
import math

# Optional dependencies with graceful fallbacks
try:
    from PIL import Image, ImageDraw, ImageTk
    PIL_AVAILABLE = True
    IMAGETK_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False
    IMAGETK_AVAILABLE = False

try:
    import pystray
    from pystray import MenuItem as item
    TRAY_AVAILABLE = PIL_AVAILABLE  # Tray needs PIL for icons
except ImportError:
    TRAY_AVAILABLE = False


class AdvancedTimeCalculator:
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

    def setup_window(self):
        """Configure main window with optimized layout"""
        self.root.title("🕐 Advanced Time Calculator")
        # Reduced width to align with tray button + margins, increased height for 50% more results space
        self.root.geometry("750x1200")
        self.root.configure(bg='#ecf0f1')  # Modern light background
        self.root.minsize(725, 850)  # Adjusted minimum size
        self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
        
        # Add subtle window styling
        try:
            self.root.attributes('-alpha', 0.98)  # Slight transparency for modern look
        except:
            pass  # Not supported on all systems

    def create_icon(self):
        """Create application icon"""
        if not PIL_AVAILABLE:
            self.root.title("🕐 Advanced Time Calculator")
            self.icon_image = None
            return
            
        try:
            size = 64
            image = Image.new('RGBA', (size, size), (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Clock face
            margin = 4
            draw.ellipse([margin, margin, size-margin, size-margin], 
                        fill='#2c3e50', outline='#34495e', width=2)
            
            center = size // 2
            
            # Clock hands
            draw.line([center, center, center + 12, center], fill='white', width=4)
            draw.line([center, center, center, center - 16], fill='white', width=3)
            
            # Hour markers
            for hour in range(12):
                angle_rad = math.radians(hour * 30 - 90)
                outer_x = center + 20 * math.cos(angle_rad)
                outer_y = center + 20 * math.sin(angle_rad)
                inner_x = center + 16 * math.cos(angle_rad)
                inner_y = center + 16 * math.sin(angle_rad)
                draw.line([inner_x, inner_y, outer_x, outer_y], fill='white', width=2)
            
            # Center dot
            draw.ellipse([center-3, center-3, center+3, center+3], fill='white')
            
            # Calculator symbol
            calc_x, calc_y = size - 16, size - 16
            draw.rectangle([calc_x, calc_y, calc_x + 12, calc_y + 12], 
                          fill='#3498db', outline='#2980b9')
            plus_x, plus_y = calc_x + 6, calc_y + 6
            draw.line([plus_x - 3, plus_y, plus_x + 3, plus_y], fill='white', width=2)
            draw.line([plus_x, plus_y - 3, plus_x, plus_y + 3], fill='white', width=2)
            
            # Set window icon
            if IMAGETK_AVAILABLE:
                self.window_icon = ImageTk.PhotoImage(image)
                self.root.iconphoto(True, self.window_icon)
            
            self.icon_image = image
            
        except Exception as e:
            print(f"Icon creation failed: {e}")
            self.root.title("🕐 Advanced Time Calculator")
            self.icon_image = None

    def setup_styles(self):
        """Configure modern styling"""
        self.style = ttk.Style()
        self.style.theme_use('clam')
        
        # Define modern color scheme
        self.colors = {
            'primary': '#2c3e50',      # Dark blue-gray
            'secondary': '#3498db',     # Blue
            'accent': '#e74c3c',        # Red
            'success': '#27ae60',        # Green
            'warning': '#f39c12',       # Orange
            'background': '#ecf0f1',    # Light gray
            'surface': '#ffffff',       # White
            'text': '#2c3e50',          # Dark text
            'text_light': '#7f8c8d',    # Light text
            'border': '#bdc3c7'         # Light border
        }
        
        # Configure modern styles
        self.style.configure('Title.TLabel', 
                           font=('Segoe UI', 20, 'bold'),
                           foreground=self.colors['primary'])
        
        self.style.configure('Subtitle.TLabel',
                           font=('Segoe UI', 10),
                           foreground=self.colors['text_light'])
        
        self.style.configure('Modern.TLabelFrame',
                           background=self.colors['surface'],
                           borderwidth=1,
                           relief='solid')
        
        self.style.configure('Modern.TLabelFrame.Label',
                           font=('Segoe UI', 11, 'bold'),
                           foreground=self.colors['primary'],
                           background=self.colors['surface'])
        
        self.style.configure('Primary.TButton',
                           font=('Segoe UI', 10, 'bold'),
                           foreground='white',
                           background=self.colors['secondary'],
                           borderwidth=0,
                           focuscolor='none')
        
        self.style.map('Primary.TButton',
                      background=[('active', '#2980b9'),
                                 ('pressed', '#21618c')])
        
        self.style.configure('Secondary.TButton',
                           font=('Segoe UI', 9),
                           foreground=self.colors['text'],
                           background=self.colors['surface'],
                           borderwidth=1,
                           focuscolor='none')
        
        self.style.map('Secondary.TButton',
                      background=[('active', self.colors['background']),
                                 ('pressed', self.colors['border'])])
        
        self.style.configure('Success.TButton',
                           font=('Segoe UI', 9, 'bold'),
                           foreground='white',
                           background=self.colors['success'],
                           borderwidth=0,
                           focuscolor='none')
        
        self.style.map('Success.TButton',
                      background=[('active', '#229954'),
                                 ('pressed', '#1e8449')])
        
        # Configure status bar
        self.style.configure('Status.TLabel',
                           font=('Segoe UI', 9),
                           foreground=self.colors['text_light'],
                           background=self.colors['border'],
                           relief='sunken',
                           borderwidth=1)

    def create_interface(self):
        """Create modern interface"""
        # Main container with modern padding
        main_frame = ttk.Frame(self.root, padding="25")
        main_frame.pack(fill=tk.BOTH, expand=True)

        self.create_header(main_frame)
        self.create_input_section(main_frame)
        self.create_buttons(main_frame)
        self.create_results_section(main_frame)
        self.create_status_bar(main_frame)

    def create_header(self, parent):
        """Create modern header with better typography"""
        header = ttk.Frame(parent)
        header.pack(fill=tk.X, pady=(0, 25))

        # Main title with modern styling
        title_label = ttk.Label(header, text="🕐 Advanced Time Calculator", 
                               style='Title.TLabel')
        title_label.pack(anchor='w')
        
        # Subtitle with better spacing
        subtitle_label = ttk.Label(header, 
                                  text="Time arithmetic with progress estimation • Press Enter to calculate",
                                  style='Subtitle.TLabel')
        subtitle_label.pack(anchor='w', pady=(8, 0))

    def create_input_section(self, parent):
        """Create modern input area"""
        input_frame = ttk.LabelFrame(parent, text="📝 Calculation Input", padding="20")
        input_frame.pack(fill=tk.X, pady=(0, 20))

        # Input label with better styling
        input_label = ttk.Label(input_frame, text="Enter your calculation:", 
                              font=('Segoe UI', 10, 'bold'),
                              foreground=self.colors['text'])
        input_label.pack(anchor='w', pady=(0, 8))
        
        # Modern text input with better styling (compact for narrower window)
        self.input_text = tk.Text(input_frame, height=3, 
                                 font=('Consolas', 12), 
                                 wrap=tk.WORD,
                                 bg=self.colors['surface'],
                                 fg=self.colors['text'],
                                 relief='solid',
                                 borderwidth=1,
                                 highlightthickness=2,
                                 highlightcolor=self.colors['secondary'],
                                 highlightbackground=self.colors['border'])
        self.input_text.pack(fill=tk.X, pady=(0, 15))

        # Modern examples section
        examples = """💡 Examples:
• now + 30m                     • 2:56am + 3.5h                 • 2025-08-19 17:00:15 + 17m
• 14:30 - 1h 15m               • 2025/12/25 - now              • 12:00pm + 2w 3d 4.5h
• 3d + now                     • 45m * 2 + now                 • 3 * 2h 30m
• 1h15s@15% (total time)       • progress(2h30m45s, 35%)       • 15% in 1h15s
• 4:30p + 1h                   • 3s + 4:30pm                   • 9:15a + 2h
• 2h30m @ 1.5GB -> 10GB        • 45m @ 500MB -> 2GB            • 1h15s @ 2.3TB -> 15TB"""

        examples_label = ttk.Label(input_frame, text=examples, 
                                  font=('Segoe UI', 9),
                                  foreground=self.colors['text_light'])
        examples_label.pack(anchor='w')

    def create_buttons(self, parent):
        """Create modern button layout"""
        buttons = ttk.Frame(parent)
        buttons.pack(fill=tk.X, pady=(0, 20))

        # Primary action button (Calculate)
        calc_btn = ttk.Button(buttons, text="🚀 Calculate", 
                              command=self.calculate, style='Primary.TButton')
        calc_btn.pack(side=tk.LEFT, padx=(0, 12))
        
        # Secondary buttons
        clear_btn = ttk.Button(buttons, text="🗑️ Clear", 
                              command=self.clear_input, style='Secondary.TButton')
        clear_btn.pack(side=tk.LEFT, padx=(0, 12))
        
        now_btn = ttk.Button(buttons, text="⏰ Insert 'now'", 
                            command=self.insert_now, style='Secondary.TButton')
        now_btn.pack(side=tk.LEFT, padx=(0, 12))
        
        help_btn = ttk.Button(buttons, text="❓ Help (F1)", 
                             command=self.show_help, style='Secondary.TButton')
        help_btn.pack(side=tk.LEFT, padx=(0, 12))
        
        # Tray button if available
        if TRAY_AVAILABLE:
            tray_btn = ttk.Button(buttons, text="📌 Minimize to Tray", 
                                 command=self.hide_window, style='Success.TButton')
            tray_btn.pack(side=tk.LEFT)

    def create_results_section(self, parent):
        """Create modern results area"""
        results_frame = ttk.LabelFrame(parent, text="📊 Results", padding="20")
        results_frame.pack(fill=tk.BOTH, expand=True, pady=(0, 15))

        text_frame = ttk.Frame(results_frame)
        text_frame.pack(fill=tk.BOTH, expand=True)

        # Modern results text area with 50% more height
        self.results_text = tk.Text(text_frame, 
                                   font=('Consolas', 11), 
                                   wrap=tk.WORD,
                                   state=tk.DISABLED, 
                                   bg=self.colors['surface'],
                                   fg=self.colors['text'],
                                   relief='solid',
                                   borderwidth=1,
                                   highlightthickness=0,
                                   padx=10,
                                   pady=10,
                                   height=20)  # Increased from default ~13 to 20 (50% more)
        
        # Modern scrollbar
        scrollbar = ttk.Scrollbar(text_frame, orient=tk.VERTICAL, 
                                 command=self.results_text.yview)
        self.results_text.configure(yscrollcommand=scrollbar.set)

        self.results_text.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.show_welcome()

    def create_status_bar(self, parent):
        """Create modern status bar"""
        self.status_var = tk.StringVar(value="✅ Ready • Enter calculation and press Enter")
        status_label = ttk.Label(parent, textvariable=self.status_var, 
                                anchor=tk.W, padding=(10, 8))
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
        """Setup system tray"""
        if not TRAY_AVAILABLE:
            return
            
        try:
            menu = pystray.Menu(
                item('Open Calculator', self.show_window),
                item('Quick Calculate', self.quick_calculate),
                pystray.Menu.SEPARATOR,
                item('Current Time', self.show_current_time),
                item('Help', self.show_help),
                pystray.Menu.SEPARATOR,
                item('Exit', self.quit_application)
            )
            
            self.tray_icon = pystray.Icon("time_calculator", self.icon_image, 
                                         "Advanced Time Calculator", menu)
            
            threading.Thread(target=self.tray_icon.run, daemon=True).start()
            
        except Exception as e:
            print(f"Tray setup failed: {e}")
            self.tray_icon = None

    # Window management
    def on_closing(self):
        if TRAY_AVAILABLE and self.tray_icon:
            self.hide_window()
        else:
            self.quit_application()

    def hide_window(self):
        self.root.withdraw()
        self.is_hidden = True

    def show_window(self):
        self.root.deiconify()
        self.root.lift()
        self.root.focus_force()
        self.is_hidden = False

    def toggle_window(self):
        self.show_window() if self.is_hidden else self.hide_window()

    def quit_application(self):
        if self.tray_icon:
            self.tray_icon.stop()
        self.root.quit()
        self.root.destroy()

    # Tray functions
    def quick_calculate(self):
        if not TRAY_AVAILABLE:
            return
            
        dialog = tk.Toplevel()
        dialog.title("Quick Calculation")
        dialog.geometry("450x170")
        dialog.resizable(False, False)
        dialog.transient(self.root)
        dialog.grab_set()
        
        tk.Label(dialog, text="Enter calculation:", font=('Arial', 10)).pack(pady=10)
        
        entry = tk.Entry(dialog, font=('Consolas', 11), width=50)
        entry.pack(pady=5)
        entry.focus_set()
        
        result_label = tk.Label(dialog, text="", font=('Arial', 9), wraplength=420)
        result_label.pack(pady=10)
        
        def calc():
            try:
                expr = entry.get().strip()
                if expr:
                    result = self.parse_and_calculate(expr)
                    if isinstance(result, timedelta):
                        result_label.config(text=self.format_friendly(result))
                    else:
                        result_label.config(text=f"Result: {result.strftime('%Y-%m-%d %H:%M:%S')}")
            except Exception as e:
                result_label.config(text=f"Error: {str(e)}")
        
        btn_frame = tk.Frame(dialog)
        btn_frame.pack(pady=10)
        tk.Button(btn_frame, text="Calculate", command=calc).pack(side=tk.LEFT, padx=5)
        tk.Button(btn_frame, text="Close", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        entry.bind('<Return>', lambda e: calc())

    def show_current_time(self):
        if TRAY_AVAILABLE:
            try:
                self.tray_icon.notify("Current Time", 
                                     datetime.now().strftime("%Y-%m-%d %H:%M:%S"), 
                                     timeout=3)
            except Exception as e:
                print(f"Notification failed: {e}")

    # Input handling
    def insert_now(self):
        now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.input_text.insert(tk.INSERT, now)
        self.input_text.focus_set()

    def clear_input(self):
        self.input_text.delete('1.0', tk.END)
        self.input_text.focus_set()

    def calculate(self):
        """Main calculation function"""
        try:
            expression = self.input_text.get('1.0', tk.END).strip()
            if not expression:
                self.status_var.set("⚠️ Please enter a calculation")
                return

            self.status_var.set("🔄 Calculating...")
            self.root.update()

            result = self.parse_and_calculate(expression)
            self.display_results(expression, result)
            self.status_var.set("✅ Calculation completed")

        except Exception as e:
            self.status_var.set(f"❌ Error: {str(e)}")
            messagebox.showerror("Calculation Error", 
                               f"Unable to process:\n\n{str(e)}\n\nPlease check input format.")

    # Core parsing and calculation
    def parse_and_calculate(self, expression):
        """Main calculation engine"""
        # Clean expression
        expression = expression.replace('\n', ' ').replace('\r', '').strip()

        # Replace 'now' with current timestamp
        if 'now' in expression.lower():
            now_str = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
            expression = re.sub(r'\bnow\b', now_str, expression, flags=re.IGNORECASE)

        # Check for rate calculation syntax: time @ data -> total_data
        rate_match = re.match(r'^(.+?)\s*@\s*(.+?)\s*->\s*(.+?)$', expression.strip())
        if rate_match:
            return self.calculate_data_rate(rate_match.group(1), rate_match.group(2), rate_match.group(3))

        # Handle progress syntax
        expression = self.convert_progress_syntax(expression)

        # Check if this is a progress function
        if self.is_progress_function(expression):
            return self.calculate_progress(expression)

        # Tokenize for arithmetic operations
        tokens = self.tokenize(expression)

        if len(tokens) < 3:
            if len(tokens) == 1 and self.is_progress_function(tokens[0]):
                return self.calculate_progress(tokens[0])
            raise ValueError("Expression must contain at least one operator")

        # Process the calculation
        return self.evaluate_tokens(tokens)

    def convert_progress_syntax(self, expression):
        """Convert @ and 'in' syntax to progress functions"""
        # Pattern for compound durations: 1h15s, 2d30m45s, etc.
        duration_pattern = r'[0-9]+(?:\.[0-9]+)?[a-zA-Z]+(?:[0-9]+(?:\.[0-9]+)?[a-zA-Z]+)*'
        
        # Convert @ syntax: "1h15s@15%" -> "progress(1h15s, 15%)"
        at_pattern = r'({duration_pattern})\s*@\s*([0-9]+(?:\.[0-9]+)?)%'
        expression = re.sub(at_pattern, r'progress(\1, \2%)', expression)
        
        # Convert "% in" syntax: "15% in 1h15s" -> "progress(1h15s, 15%)"
        in_pattern = r'([0-9]+(?:\.[0-9]+)?)%\s+in\s+({duration_pattern})'
        expression = re.sub(in_pattern, r'progress(\2, \1%)', expression)
        
        return expression

    def is_progress_function(self, text):
        """Check if text is a progress function call"""
        return re.match(r'^\s*progress\s*\([^)]+\)\s*$', text, re.IGNORECASE) is not None

    def calculate_progress(self, progress_expr):
        """Calculate progress estimates"""
        # Parse: progress(duration, percentage[, mode])
        pattern = r'progress\s*\(\s*([^,]+)\s*,\s*([0-9]+(?:\.[0-9]+)?)%(?:\s*,\s*(\w+))?\s*\)'
        match = re.match(pattern, progress_expr, re.IGNORECASE)
        
        if not match:
            raise ValueError("Invalid progress syntax")
        
        duration_str = match.group(1).strip()
        percentage = float(match.group(2))
        mode = (match.group(3) or 'total').lower()
        
        if not (0 < percentage < 100):
            raise ValueError("Percentage must be between 0 and 100")
        
        # Parse elapsed duration
        elapsed = self.parse_duration(duration_str)
        elapsed_seconds = elapsed.total_seconds()
        
        # Calculate total and remaining
        total_seconds = elapsed_seconds / (percentage / 100.0)
        remaining_seconds = total_seconds - elapsed_seconds
        
        if mode == 'total':
            return timedelta(seconds=total_seconds)
        elif mode == 'remaining':
            return timedelta(seconds=remaining_seconds)
        elif mode == 'eta':
            return datetime.now() + timedelta(seconds=remaining_seconds)
        else:
            raise ValueError(f"Invalid mode: {mode}")

    def tokenize(self, expression):
        """Tokenize expression while preserving function calls"""
        # Don't tokenize function calls
        if self.is_progress_function(expression):
            return [expression]
            
        tokens = []
        current = ""
        paren_depth = 0
        
        for char in expression:
            if char == '(':
                paren_depth += 1
                current += char
            elif char == ')':
                paren_depth -= 1
                current += char
            elif char in '+-*' and paren_depth == 0:
                if self.is_operator_here(expression, current, char):
                    if current.strip():
                        tokens.append(current.strip())
                    tokens.append(char)
                    current = ""
                else:
                    current += char
            else:
                current += char
        
        if current.strip():
            tokens.append(current.strip())
        
        return tokens

    def is_operator_here(self, expression, before, char):
        """Determine if character is an operator in context"""
        if not before.strip():
            return False
        
        # Don't split dates like 2025-08-19
        if char == '-':
            if re.search(r'\d{4}$', before) or re.search(r'\d{4}-\d{2}$', before):
                return False
        
        # Multiplication is always an operator
        if char == '*':
            return True
            
        # Check for datetime patterns
        if self.looks_like_datetime(before.strip()):
            return True
            
        # Look for surrounding whitespace
        return ' ' in before or expression.find(before + char + ' ') != -1

    def looks_like_datetime(self, text):
        """Enhanced datetime pattern detection"""
        patterns = [
            r'^\d{4}[-/]\d{2}[-/]\d{2}(\s+\d{1,2}:\d{2}(:\d{2})?(\s*[ap]m?)?)?$',
            r'^\d{1,2}/\d{1,2}/\d{4}(\s+\d{1,2}:\d{2}(:\d{2})?(\s*[ap]m?)?)?$',
            r'^\d{1,2}:\d{2}(:\d{2})?(\s*[ap]m?)?$',  # Include 'a'/'p' support
        ]
        return any(re.match(p, text, re.IGNORECASE) for p in patterns)

    def evaluate_tokens(self, tokens):
        """Evaluate tokenized expression"""
        # Parse first token
        if self.is_number(tokens[0]) and len(tokens) >= 3 and tokens[1] == '*':
            result = float(tokens[0])
        else:
            first = self.parse_value(tokens[0])
            # Handle duration + datetime pattern
            if isinstance(first, timedelta) and len(tokens) >= 3 and tokens[1] == '+':
                second = self.parse_value(tokens[2])
                if isinstance(second, datetime):
                    return second + first
            result = first

        # Process operations
        i = 1
        while i < len(tokens) - 1:
            op = tokens[i]
            operand = self.parse_value(tokens[i + 1])
            
            if op == '+':
                result = self.add_values(result, operand)
            elif op == '-':
                result = self.subtract_values(result, operand)
            elif op == '*':
                result = self.multiply_values(result, operand)
            else:
                raise ValueError(f"Unknown operator: {op}")
            
            i += 2
        
        return result

    def add_values(self, a, b):
        """Add two values with enhanced type checking"""
        if isinstance(a, datetime) and isinstance(b, timedelta):
            return a + b
        elif isinstance(a, timedelta) and isinstance(b, datetime):
            return b + a
        elif isinstance(a, timedelta) and isinstance(b, timedelta):
            return a + b
        elif isinstance(a, datetime) and isinstance(b, datetime):
            # Handle time-only additions - check if b is time-only
            if b.date() == datetime(1900, 1, 1).date():
                # b is time-only, add its time components to a
                return a + timedelta(hours=b.hour, minutes=b.minute, 
                                   seconds=b.second, microseconds=b.microsecond)
            else:
                # Both are full datetimes, add b's offset from epoch
                return a + (b - datetime(1900, 1, 1))
        else:
            raise ValueError(f"Cannot add {type(a).__name__} and {type(b).__name__}")

    def subtract_values(self, a, b):
        """Subtract two values with type checking"""
        if isinstance(a, datetime) and isinstance(b, datetime):
            return a - b
        elif isinstance(a, datetime) and isinstance(b, timedelta):
            return a - b
        elif isinstance(a, timedelta) and isinstance(b, timedelta):
            return a - b
        else:
            raise ValueError("Invalid subtraction")

    def multiply_values(self, a, b):
        """Multiply values with type checking"""
        if isinstance(a, (int, float)) and isinstance(b, timedelta):
            return b * a
        elif isinstance(a, timedelta) and isinstance(b, (int, float)):
            return a * b
        else:
            raise ValueError("Can only multiply number × duration")

    def parse_value(self, text):
        """Parse a single value (datetime, duration, or number)"""
        text = text.strip()
        
        if text.lower() == 'now':
            return datetime.now()
        
        if self.is_number(text):
            return float(text)
            
        if self.is_datetime_format(text):
            return self.parse_datetime(text)
        else:
            return self.parse_duration(text)

    def is_number(self, text):
        """Check if text is a number"""
        try:
            float(text)
            return True
        except ValueError:
            return False

    def is_datetime_format(self, text):
        """Enhanced datetime format detection"""
        # Check for time patterns (including AM/PM variations)
        time_patterns = [
            r'\d{1,2}:\d{2}(:\d{2})?(\.\d+)?(\s*[ap]m?)?',  # Support both 'a'/'p' and 'am'/'pm'
            r'\d{4}[-/]\d{2}[-/]\d{2}',  # Date patterns
            r'\d{1,2}/\d{1,2}/\d{4}',    # US date format
        ]
        
        return any(re.search(pattern, text, re.IGNORECASE) for pattern in time_patterns)

    def parse_datetime(self, time_str):
        """Enhanced datetime parsing with 'a'/'p' support"""
        time_str = time_str.strip()
        
        # Normalize 'a' and 'p' to 'am' and 'pm' before parsing
        time_str = re.sub(r'([ap])(?:\s|$)', r'\1m', time_str, flags=re.IGNORECASE)
        
        formats = [
            "%Y-%m-%d %H:%M:%S.%f", "%Y-%m-%d %H:%M:%S", "%Y-%m-%d %H:%M",
            "%Y-%m-%d %I:%M:%S %p", "%Y-%m-%d %I:%M %p",
            "%Y/%m/%d %H:%M:%S.%f", "%Y/%m/%d %H:%M:%S", "%Y/%m/%d %H:%M",
            "%Y/%m/%d %I:%M:%S %p", "%Y/%m/%d %I:%M %p",
            "%m/%d/%Y %H:%M:%S", "%m/%d/%Y %H:%M", "%m/%d/%Y %I:%M %p",
            "%H:%M:%S.%f", "%H:%M:%S", "%H:%M", "%I:%M:%S %p", "%I:%M %p",
            "%Y-%m-%d", "%Y/%m/%d", "%m/%d/%Y"
        ]
        
        for fmt in formats:
            try:
                return datetime.strptime(time_str, fmt)
            except ValueError:
                continue
        
        # Enhanced decimal seconds handling with 'a'/'p' support
        decimal_patterns = [
            r'^(\d{1,2}):(\d{2}):(\d{1,2}(?:\.\d+)?)(?:\s*(am|pm))?$',
            r'^(\d{1,2}):(\d{2})(?:\s*(am|pm))?$',  # Handle minutes-only times
        ]
        
        for pattern in decimal_patterns:
            match = re.match(pattern, time_str, re.IGNORECASE)
            if match:
                hours = int(match.group(1))
                minutes = int(match.group(2))
                
                # Handle seconds (may not be present)
                if len(match.groups()) >= 4 and match.group(3):  # Pattern with seconds
                    seconds_float = float(match.group(3))
                    ampm = match.group(4) if match.group(4) else None
                else:  # Pattern without seconds
                    seconds_float = 0.0
                    ampm = match.group(3) if len(match.groups()) >= 3 and match.group(3) else None
                
                # Validate components
                if minutes >= 60 or seconds_float >= 60:
                    raise ValueError(f"Invalid time: {minutes}m {seconds_float}s")
                
                # Handle AM/PM
                if ampm:
                    if not (1 <= hours <= 12):
                        raise ValueError(f"Invalid 12-hour format: {hours}")
                    if ampm.lower() in ['pm', 'p'] and hours != 12:
                        hours += 12
                    elif ampm.lower() in ['am', 'a'] and hours == 12:
                        hours = 0
                elif hours >= 24:
                    raise ValueError(f"Invalid 24-hour format: {hours}")
                
                seconds = int(seconds_float)
                microseconds = int((seconds_float - seconds) * 1000000)
                return datetime(1900, 1, 1, hours, minutes, seconds, microseconds)
        
        raise ValueError(f"Cannot parse datetime: {time_str}")

    def parse_duration(self, duration_str):
        """Parse duration strings including compound formats like 1h15s"""
        duration_str = duration_str.strip().lower()
        
        # Simple decimal hours
        if re.match(r'^[0-9]+(?:\.[0-9]+)?h$', duration_str):
            return timedelta(hours=float(duration_str[:-1]))
        
        # Parse compound durations
        total = timedelta()
        
        # Find all time components
        patterns = {
            r'([0-9]+(?:\.[0-9]+)?)y': lambda x: timedelta(days=float(x) * 365.25),
            r'([0-9]+(?:\.[0-9]+)?)mo': lambda x: timedelta(days=float(x) * 30.44),
            r'([0-9]+(?:\.[0-9]+)?)w': lambda x: timedelta(weeks=float(x)),
            r'([0-9]+(?:\.[0-9]+)?)d': lambda x: timedelta(days=float(x)),
            r'([0-9]+(?:\.[0-9]+)?)h': lambda x: timedelta(hours=float(x)),
            r'([0-9]+(?:\.[0-9]+)?)m(?!o)': lambda x: timedelta(minutes=float(x)),
            r'([0-9]+(?:\.[0-9]+)?)s': lambda x: timedelta(seconds=float(x))
        }
        
        found_any = False
        for pattern, converter in patterns.items():
            matches = re.findall(pattern, duration_str)
            for match in matches:
                total += converter(match)
                found_any = True
        
        if not found_any:
            raise ValueError(f"Cannot parse duration: {duration_str}")
        
        return total

    def parse_data_amount(self, data_str):
        """Parse data amounts with various units (KB, MB, GB, TB, KiB, MiB, GiB, TiB)"""
        data_str = data_str.strip()
        
        # Pattern to match number + unit
        pattern = r'^([0-9]+(?:\.[0-9]+)?)\s*([KMGTP]?[i]?[B])$'
        match = re.match(pattern, data_str, re.IGNORECASE)
        
        if not match:
            raise ValueError(f"Cannot parse data amount: {data_str}")
        
        value = float(match.group(1))
        unit = match.group(2).upper()
        
        # Define conversion factors (to bytes)
        factors = {
            # Decimal units (1000-based)
            'B': 1,
            'KB': 1000,
            'MB': 1000**2,
            'GB': 1000**3,
            'TB': 1000**4,
            'PB': 1000**5,
            # Binary units (1024-based)
            'KIB': 1024,
            'MIB': 1024**2,
            'GIB': 1024**3,
            'TIB': 1024**4,
            'PIB': 1024**5,
        }
        
        if unit not in factors:
            raise ValueError(f"Unknown data unit: {unit}")
        
        return value * factors[unit]

    def format_data_amount(self, bytes_value):
        """Format bytes into human-readable data amounts"""
        if bytes_value == 0:
            return "0 B"
        
        # Define units and their factors
        units = [
            ('PB', 1000**5),
            ('TB', 1000**4),
            ('GB', 1000**3),
            ('MB', 1000**2),
            ('KB', 1000),
            ('B', 1)
        ]
        
        for unit, factor in units:
            if bytes_value >= factor:
                value = bytes_value / factor
                if value >= 100:
                    return f"{value:.0f} {unit}"
                elif value >= 10:
                    return f"{value:.1f} {unit}"
                else:
                    return f"{value:.2f} {unit}"
        
        return f"{bytes_value} B"

    def format_data_rate(self, bytes_per_second):
        """Format data transfer rate"""
        if bytes_per_second == 0:
            return "0 B/s"
        
        # Format as rate
        rate_str = self.format_data_amount(bytes_per_second)
        return f"{rate_str}/s"

    def calculate_data_rate(self, elapsed_time_str, data_amount_str, total_data_str):
        """Calculate time needed for data transfer based on rate"""
        try:
            # Parse elapsed time
            elapsed_time = self.parse_duration(elapsed_time_str.strip())
            elapsed_seconds = elapsed_time.total_seconds()
            
            # Parse data amounts
            data_amount_bytes = self.parse_data_amount(data_amount_str.strip())
            total_data_bytes = self.parse_data_amount(total_data_str.strip())
            
            if elapsed_seconds <= 0:
                raise ValueError("Elapsed time must be positive")
            
            if data_amount_bytes <= 0:
                raise ValueError("Data amount must be positive")
            
            if total_data_bytes <= 0:
                raise ValueError("Total data amount must be positive")
            
            # Calculate transfer rate (bytes per second)
            transfer_rate = data_amount_bytes / elapsed_seconds
            
            # Calculate time needed for total data
            total_time_seconds = total_data_bytes / transfer_rate
            total_time = timedelta(seconds=total_time_seconds)
            
            # Return a special result object that includes rate information
            return {
                'type': 'data_rate',
                'total_time': total_time,
                'transfer_rate': transfer_rate,
                'elapsed_time': elapsed_time,
                'data_amount': data_amount_bytes,
                'total_data': total_data_bytes
            }
            
        except Exception as e:
            raise ValueError(f"Data rate calculation error: {str(e)}")

    # Display methods
    def show_welcome(self):
        """Show welcome message"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)
        
        welcome = """🕐 Advanced Time Calculator

✨ Features:
✓ Multiple date/time formats (YYYY-MM-DD, YYYY/MM/DD, MM/DD/YYYY)
✓ Duration units with decimal precision (3.5h, 2.25d, 45.5s)
✓ Compound durations (1d45m15s, 2h30m45s)
✓ Current time with 'now' keyword
✓ Scalar multiplication (3 * 2h 30m)
✓ Flexible operations (3d + now, 45m * 2 + now)
✓ Progress estimation (1h15s@15%, progress(2h30m, 35%))
✓ AM/PM shorthand support (4:30p, 9:15a)
✓ Data transfer rate calculations (2h30m @ 1.5GB -> 10GB)
✓ System tray integration

🚀 Quick Examples:
• now + 30m
• 2025-12-25 - now
• 1h15s@15% (total time if 15% done in 1h15s)
• progress(2h30m45s, 35%, remaining)
• 4:30p + 1h
• 3s + 4:30pm
• 2h30m @ 1.5GB -> 10GB (data transfer estimation)"""

        self.results_text.insert(tk.END, welcome)
        self.results_text.config(state=tk.DISABLED)

    def display_results(self, expression, result):
        """Display results"""
        self.results_text.config(state=tk.NORMAL)
        self.results_text.delete('1.0', tk.END)
        
        # Header
        self.results_text.insert(tk.END, "=" * 69 + "\n")
        self.results_text.insert(tk.END, f"CALCULATION: {expression}\n")
        self.results_text.insert(tk.END, "=" * 69 + "\n\n")
        
        if isinstance(result, dict) and result.get('type') == 'data_rate':
            self.display_data_rate_result(result, expression)
        elif isinstance(result, timedelta):
            self.display_duration_result(result, expression)
        else:
            self.display_datetime_result(result)
        
        self.results_text.insert(tk.END, "\n" + "=" * 69)
        self.results_text.config(state=tk.DISABLED)
        self.results_text.see('1.0')

    def display_data_rate_result(self, result, expression):
        """Display data transfer rate calculation results"""
        self.results_text.insert(tk.END, "📊 DATA TRANSFER CALCULATION\n")
        self.results_text.insert(tk.END, "-" * 50 + "\n\n")
        
        # Extract data from result
        total_time = result['total_time']
        transfer_rate = result['transfer_rate']
        elapsed_time = result['elapsed_time']
        data_amount = result['data_amount']
        total_data = result['total_data']
        
        # Display total time needed
        total_seconds = total_time.total_seconds()
        days = int(total_seconds // 86400)
        hours = int((total_seconds % 86400) // 3600)
        minutes = int((total_seconds % 3600) // 60)
        seconds = total_seconds % 60
        
        self.results_text.insert(tk.END, f"⏱️  Total Time Needed: {days}d {hours}h {minutes}m {seconds:.1f}s\n")
        self.results_text.insert(tk.END, f"📈 Transfer Rate: {self.format_data_rate(transfer_rate)}\n\n")
        
        # Display calculation details
        self.results_text.insert(tk.END, "📋 Calculation Details:\n")
        self.results_text.insert(tk.END, "-" * 30 + "\n")
        self.results_text.insert(tk.END, f"Elapsed Time: {self.format_friendly(elapsed_time)}\n")
        self.results_text.insert(tk.END, f"Data Transferred: {self.format_data_amount(data_amount)}\n")
        self.results_text.insert(tk.END, f"Total Data Needed: {self.format_data_amount(total_data)}\n\n")
        
        # Progress analysis
        progress_pct = (data_amount / total_data) * 100
        remaining_pct = 100 - progress_pct
        remaining_data = total_data - data_amount
        
        self.results_text.insert(tk.END, "📊 Progress Analysis:\n")
        self.results_text.insert(tk.END, "-" * 30 + "\n")
        self.results_text.insert(tk.END, f"Progress: {progress_pct:.1f}% complete\n")
        self.results_text.insert(tk.END, f"Remaining: {self.format_data_amount(remaining_data)} ({remaining_pct:.1f}%)\n")
        self.results_text.insert(tk.END, f"Time Remaining: {self.format_friendly(total_time)}\n\n")
        
        # ETA calculation
        eta = datetime.now() + total_time
        self.results_text.insert(tk.END, f"🎯 Estimated Completion: {eta.strftime('%Y-%m-%d %H:%M:%S')}\n")

    def display_duration_result(self, duration, expression):
        """Display duration with progress analysis"""
        self.results_text.insert(tk.END, "⏱️  DURATION RESULT\n")
        self.results_text.insert(tk.END, "-" * 50 + "\n\n")
        
        total_seconds = duration.total_seconds()
        abs_seconds = abs(total_seconds)
        
        days = int(abs_seconds // 86400)
        hours = int((abs_seconds % 86400) // 3600)
        minutes = int((abs_seconds % 3600) // 60)
        seconds = abs_seconds % 60
        
        sign = "-" if total_seconds < 0 else ""
        
        self.results_text.insert(tk.END, f"Duration: {sign}{days}d {hours}h {minutes}m {seconds:.3f}s\n")
        self.results_text.insert(tk.END, f"Friendly: {self.format_friendly(duration)}\n\n")
        
        # Progress analysis
        if any(keyword in expression.lower() for keyword in ['progress(', '@', '% in']):
            self.results_text.insert(tk.END, "📊 PROGRESS ANALYSIS\n")
            self.results_text.insert(tk.END, "-" * 40 + "\n")
            
            if 'eta' in expression.lower():
                eta = datetime.now() + duration
                self.results_text.insert(tk.END, f"Completion time: {eta.strftime('%Y-%m-%d %H:%M:%S')}\n")
            elif 'remaining' in expression.lower():
                self.results_text.insert(tk.END, f"Time remaining: {self.format_friendly(duration)}\n")
                if total_seconds > 0:
                    eta = datetime.now() + duration
                    self.results_text.insert(tk.END, f"Completion: {eta.strftime('%Y-%m-%d %H:%M:%S')}\n")
            else:
                self.results_text.insert(tk.END, f"Total duration: {self.format_friendly(duration)}\n")
                # Extract percentage for context
                percent_match = re.search(r'(\d+(?:\.\d+)?)%', expression)
                if percent_match:
                    percent = float(percent_match.group(1))
                    remaining_pct = 100 - percent
                    remaining = duration * (remaining_pct / 100)
                    eta = datetime.now() + remaining
                    self.results_text.insert(tk.END, f"Remaining ({remaining_pct:.1f}%): {self.format_friendly(remaining)}\n")
                    self.results_text.insert(tk.END, f"Completion: {eta.strftime('%Y-%m-%d %H:%M:%S')}\n")
            self.results_text.insert(tk.END, "\n")
        
        # Unit conversions
        conversions = [
            ("Total Seconds", f"{total_seconds:.3f}"),
            ("Total Minutes", f"{total_seconds/60:.3f}"),
            ("Total Hours", f"{total_seconds/3600:.3f}"),
            ("Total Days", f"{total_seconds/86400:.3f}"),
        ]
        
        for label, value in conversions:
            self.results_text.insert(tk.END, f"{label:14}: {value}\n")

    def display_datetime_result(self, dt):
        """Display datetime results"""
        self.results_text.insert(tk.END, "📅 DATE/TIME RESULT\n")
        self.results_text.insert(tk.END, "-" * 50 + "\n\n")
        
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

    def format_friendly(self, duration):
        """Format duration in friendly way"""
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
        
        if len(parts) == 1:
            return parts[0]
        elif len(parts) == 2:
            return f"{parts[0]} and {parts[1]}"
        else:
            return f"{', '.join(parts[:-1])}, and {parts[-1]}"

    def show_help(self):
        """Show comprehensive help"""
        help_text = """📖 ADVANCED TIME CALCULATOR - HELP

🕐 TIME FORMATS:
• 24-hour: 14:30, 14:30:45, 14:30:45.5
• 12-hour: 2:30pm, 2:30:45pm, 4:30p, 9:15a
• Current: now

📅 DATE FORMATS:
• ISO: 2025-08-19, 2025-08-19 14:30:45
• US: 08/19/2025, 08/19/2025 2:30pm
• International: 2025/08/19, 2025/08/19 16:51:00

⏱️ DURATION UNITS:
• y = years, mo = months, w = weeks, d = days
• h = hours, m = minutes, s = seconds
• Compound: 1h15s, 2h30m45s, 1d12h30m

🧮 OPERATIONS:
• now + 30m
• 4:30pm + 3s
• 3s + 4:30pm  
• 2025-12-25 - now
• 3d + now
• 3 * 2h 30m

📊 PROGRESS ESTIMATION:
• 1h15s@15% (total time if 15% done)
• progress(2h30m, 35%, remaining)
• 15% in 1h15s

⌨️ SHORTCUTS:
• Enter: Calculate
• Ctrl+L: Clear
• F1: Help

Examples of fixed issues:
• 3s + 4:30pm ✓
• 4:30pm + 3s ✓  
• 4:30pm + 1h ✓
• 9:15a + 2h ✓"""

        messagebox.showinfo("Help", help_text)


def main():
    """Application entry point"""
    print("🕐 Advanced Time Calculator")
    print("=" * 45)
    
    missing_deps = []
    if not PIL_AVAILABLE:
        missing_deps.append("PIL/Pillow")
    if not TRAY_AVAILABLE:
        missing_deps.append("pystray")
    
    if missing_deps:
        print("⚠️  Optional dependencies missing:")
        for dep in missing_deps:
            print(f"   • {dep}")
        print("\n📦 Install with: pip install pillow pystray")
        print("🚀 Starting with available features...\n")
    else:
        print("✅ All features available!\n")
    
    root = tk.Tk()
    app = AdvancedTimeCalculator(root)
    root.mainloop()


if __name__ == "__main__":
    main()

