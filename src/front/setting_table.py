import curses

class SettingTable:
    def __init__(self, product_info=None):
        self.product_info = product_info
        self.edit_flag = False

    def render_table(self, stdscr, table_data, selected_row, selected_col):
        rows, cols = stdscr.getmaxyx()
        stdscr.clear()
        stdscr.addstr(0, 0, "Press 'Enter' to set fields and press 'S' to save your config, or press 'M' to Exit.") 
        stdscr.addstr(rows - 1, 0, self.product_info)
        if self.edit_flag == False:
            stdscr.addstr(2, 0, 'Edit Mode (OFF)')
        else:
            stdscr.addstr(2, 0, 'Edit Mode (ON)')            

        table_width = min(cols, len(table_data[0]) * 10)
        table_height = min(rows, len(table_data) * 2)

        table_x = (cols - table_width) // 2
        table_y = (rows - table_height) // 2

        stdscr.hline(table_y, table_x, '-', table_width)
        stdscr.hline(table_y + table_height, table_x, '-', table_width)
        stdscr.vline(table_y, table_x, '|', table_height)
        stdscr.vline(table_y, table_x + table_width, '|', table_height)

        for i, row in enumerate(table_data):
            for j, cell in enumerate(row):
                x = table_x + 1 + j * 10
                y = table_y + 1 + i * 2
                if i == selected_row and j == selected_col:
                    stdscr.attron(curses.A_REVERSE)
                stdscr.addstr(y, x, str(cell))
                if i == selected_row and j == selected_col:
                    stdscr.attroff(curses.A_REVERSE)

        stdscr.refresh()

    def edit_table(self, stdscr, table_data):
        selected_row = 1
        selected_col = 2
        self.edit_flag = False

        rows, cols = stdscr.getmaxyx()

        modified_values = {}
        while True:
            self.render_table(stdscr, table_data, selected_row, selected_col)
            if self.edit_flag == False:
                stdscr.addstr(rows - 1, 0, self.product_info)
                stdscr.addstr(2, 0, 'Edit Mode (OFF)')
            key = stdscr.getch()

            if key == curses.KEY_UP:
                selected_row = max(1, selected_row - 1)
            elif key == curses.KEY_DOWN:
                selected_row = min(len(table_data) - 1, selected_row + 1)
            elif key == curses.KEY_LEFT:
                selected_col = max(2, selected_col - 1)
            elif key == curses.KEY_RIGHT:
                selected_col = min(len(table_data[0]) - 1, selected_col + 1)
            elif key == ord('\n'):
                self.edit_flag = True
                stdscr.addstr(rows - 1, 0, self.product_info)
                stdscr.addstr(2, 0, 'Edit Mode (ON)  ')
                self.edit_flag = False
                curses.echo()
                stdscr.move(selected_row * 2 + 1, selected_col * 10 + 1)
                stdscr.clrtoeol()
                value = stdscr.getstr().decode('utf-8')
                table_data[selected_row][selected_col] = value
                modified_values[table_data[selected_row][0]] = value
                curses.noecho()

            elif key == ord('s') or key == ord('S'):
                return modified_values

            elif key == ord('m') or key == ord('M'):
                return None

    def start(self, stdscr, user_info):
        curses.curs_set(0)

        table_data = [
            ['ID', 'VALUE', 'CONFIG']
        ]

        for id in user_info:
            table_data.append(
                [id, user_info[id], '  ']
            )

        modified_values = self.edit_table(stdscr, table_data)
        return modified_values
